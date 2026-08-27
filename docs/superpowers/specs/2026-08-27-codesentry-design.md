# CodeSentry 设计文档(M5-6 主力作品)

> 日期:2026-08-27 · 状态:设计已对齐,待 review → 转实施计划
> 工作名 `codesentry`(code + sentry/哨兵),可改。

## 1. 目标与定位

一个**代码感知的检索 Agent**,以 "bug 分诊 + 代码定位" 为演示场景,终点长成**多 Agent 代码审查系统**。

- **对内价值**:接现有 ClickUp 巡检,读入 bug → 定位真实 iOS 代码库的可疑文件 → 出带代码指针的分诊报告。每天真用得上。
- **对外价值(简历)**:证明"能从 harness 造起的生产级 Agent 工程师"。可迁移能力 = 对真实代码库检索+推理。
- **为什么不用 Claude Code**:用 Claude Code = agent 的用户;自建 = agent 的工程师,JD 招后者。真实公司需定制/私有/成本可控的 agent,Claude Code 不通吃。

## 2. 范围与分期

- **一期(地基)**:向量 RAG 代码定位 + 单 agent 分诊 + 评估 + 生产硬化。跑成命令行脚本。**做完即可展示。**
- **二期(长成 B)**:① 检索加 agentic 导航(向量粗召回 + agent 细读 = 混合);② 分诊换成"多专家并行审 + supervisor 汇总";③ FastAPI 服务化。

**非目标(YAGNI)**:一期不做 FastAPI、不做自动改代码/PR、不做多 worker 并发、不做 UI。

## 3. 已锁定决策

| 项 | 决策 |
|---|---|
| 目标代码库 | CoinEx 真实私有库(iOS/Swift) |
| 模型 | 云端 Kimi 为主(用户已确认;注意专有代码上云需公司政策允许) |
| 检索(一期) | 纯向量 RAG(方案①);二期加 agentic 导航→混合(③) |
| 切块 | **可插拔**:NaiveChunker(基线)→ SwiftChunker(tree-sitter AST) |
| 编排语言 | Python;二期多 agent 用 LangGraph |
| 公开 demo | 留到打包阶段,可插拔设计使"换开源 Swift repo"为配置切换 |

## 4. 项目结构

```
codesentry/
├── pyproject.toml               依赖 + 元信息(uv)
├── .env                         密钥(gitignore)
├── src/codesentry/
│   ├── chunking/                切块(可插拔)
│   │   ├── base.py              CodeChunker 接口 + CodeChunk 数据类
│   │   ├── naive.py             NaiveChunker(基线)
│   │   └── swift.py             SwiftChunker(AST)
│   ├── retrieval/               检索(embed + Chroma)
│   ├── triage/                  分诊 agent(理解/评分/报告)
│   ├── clients/                 外部客户端(ClickUp / Slack / LLM)
│   ├── eval/                    评估框架
│   └── config.py                配置
├── scripts/triage.py            命令行入口(一期)
├── tests/
└── data/eval_set.json           冻结评估集
```
原则:每文件夹一个清晰职责、能独立测试、互不侵入(切块层不知检索层长啥样)。

## 5. 数据流

**流程 A · 离线索引**(建一次,repo 变了增量更新):
遍历 .swift 文件(pathlib)→ 可插拔 chunker 切成 CodeChunk → 每块 embed → 存 Chroma(元数据带 path/行号)。增量:内容 hash 比对,只重处理改动文件。

**流程 B · 在线分诊**(每条 bug):
1. `clients/clickup` 拉 bug 标题+描述
2. `triage` LLM 结构化抽取 → {症状, 模块, 报错关键词}
3. ⭐`retrieval` 把②embed → 查 Chroma → top-k 可疑 CodeChunk(核心,评估对象)
4. `triage` 严重度评分(规则/工具,决策写死)
5. `triage` 生成结构化分诊报告(grounding,带 file:line)
6. `clients` 投递 Slack/ClickUp 评论(有副作用→幂等)

横切:config · eval(离线量准确率)· tracing(记 token/耗时/每步)。

## 6. 核心接口

```python
@dataclass
class CodeChunk:
    path: str; start_line: int; end_line: int
    symbol: str; kind: str; parent: str | None
    code: str; language: str
    # Chroma id 可用 f"{path}:{start_line}"

class CodeChunker(Protocol):
    def chunk(self, source: str, path: str) -> list[CodeChunk]: ...
    # 只吃字符串不读文件 → 纯函数、易单测;读文件由 walk_repo() 统一负责

_REGISTRY = {".swift": SwiftChunker(), ".py": PythonChunker()}
def get_chunker(path) -> CodeChunker:
    return _REGISTRY.get(suffix(path), NaiveChunker())   # 未匹配退回基线
```
加语言 = 往注册表塞一个,下游不改。

## 7. 评估设计(核心卖点)

**双评估集**(commit 未关联 ClickUp id,故不走 commit 挖真值):

- **合成集(大)**:从真实函数 → LLM 编 bug 报告 → 真值=该函数所在文件。可生成几百条,支撑 Naive-vs-Swift 大 N 对比。真值绝对准。质量闸门筛掉废描述。
- **真实金标集(小)**:用户手标 ~15-30 条真实 ClickUp bug → 正确文件。检验外部有效性。

**指标**:hit@k / MRR / Recall@k(多文件修复)。**锚在文件级**(非块/行)→ Naive vs Swift 公平比,解耦切法。冻结成 json。

**卖点实验**:同一评估集跑 Naive vs Swift AST → "AST 切块把 hit@3 从 X 提到 Y"。同时报合成 vs 真实的差距(诚实呈现局限=资深信号)。

## 8. 错误处理 / 生产硬化

**一期焊**:重试退避+抖动(429/503;400不重试)· 限流节流器(embed 批量/多bug并发撞 Kimi RPM)· 失败隔离(每条 bug try/except 不拖垮批)· 幂等(投递用 bug_id 键,已分诊状态)· 结构化 tracing 日志(每 bug 记步骤/token/耗时/检索块/严重度 → 事后算成本与延迟)· 优雅降级(相似度低→报"低置信度/无法定位",绝不硬编假位置)· 增量索引(hash 跳过未变)· 密钥进 .env · 护栏(一期只读+出报告,唯一写=投递,幂等可控)。

**留后期**:FastAPI 服务化、成本预算硬上限、多 worker。

## 9. 分工

- **✍️ 用户手写(学习关键)**:CodeChunk/CodeChunker 接口、NaiveChunker、检索逻辑、评估框架(hit@k/MRR/Recall@k)、triage 各节点、prompt、退避/幂等/tracing 核心逻辑、(二期)FastAPI、supervisor 编排。
- **🤝 我搭骨架 + 用户读懂拥有**:ClickUp/Slack 客户端接线、config、日志格式、SwiftChunker 的 tree-sitter 骨架、评估集挖取脚本的 git 部分。
- **原则**:无黑盒——整套用户都要能讲。两档=手敲(学习关键)/读懂拥有(胶水)。

## 10. 风险与开放问题

- **专有代码上云**:需确认公司政策(用户已选云端,自担;现有 Claude Code 巡检已在发代码给 Anthropic,或有先例)。
- **纯向量 RAG 短板**:自然语言 bug ↔ 代码语义鸿沟,准确率可能卡瓶颈——这正是二期加 agentic 导航的理由,且瓶颈本身是 writeup 素材。
- **SwiftChunker 难度**:tree-sitter-swift 集成是一期最硬的点,用 NaiveChunker 先跑通全链路兜底。
- **ClickUp bug 质量**:真实描述含糊,金标集要人工筛。
