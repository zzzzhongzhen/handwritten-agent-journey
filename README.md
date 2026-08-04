# handwritten-agent-journey

从零到一手写一个完整 Agent —— 一个 10 年 iOS 老兵的转型学习实录:
不依赖任何 Agent 框架,纯手写理解 Agent 本质(LLM API → Agent Loop → 工具调用 → RAG → 持久记忆)。

## 为什么手写而不用框架

做了十年 iOS,我见过太多"会用 Alamofire 但不懂 HTTP"的人——框架一换、一报错就束手无策。
转型学 Agent 时我不想重蹈覆辙:LangChain 们会过时,但 Agent 的本质(一个让 LLM 反复
"思考 → 调工具 → 看结果 → 再思考"的循环)不会。所以这个仓库里没有任何 Agent 框架,
每一行循环、每一次工具分发、每一个向量相似度都是手写的——先懂原理,再用框架,就是降维理解。

## 项目演进地图

> 按学习顺序递进,每个文件是一个阶段的产物。🎯 = 阶段里程碑

### 阶段一:Python 基础(iOS 老兵补课)
| 文件 | 内容 |
|------|------|
| `test.py` | 语法实验场:list/dict/推导式/match/集合运算,边学边踩坑 |
| `04_functions.py` | 函数、默认参数、`*args/**kwargs`、类型注解(对照 Swift) |
| `05_word_count.py` | 🎯 单词计数:dict 统计 + sorted/lambda 排序 |
| `06_exceptions.py` | try/except、精确抓异常、raise |
| `07_json_files.py` | 文件读写、JSON 序列化(dump/dumps/load/loads) |
| `08_http_requests.py` | httpx 发请求、超时与异常兜底 |
| `09_weather.py` | 🎯 天气查询:真实公开 API 全链路(请求→JSON→解析→存档) |

### 阶段二:打通大模型 API
| 文件 | 内容 |
|------|------|
| `10_hello_kimi.py` | 第一次用代码和大模型对话(messages/role/token) |
| `list_models.py` | 排障产物:查询账号实际可用的模型 |
| `11_chat_loop_kimi.py` | 🎯 多轮对话:亲手验证"大模型无状态,历史靠自己维护" |
| `12_chat_stream_kimi.py` | 流式输出:stream/delta/flush 与缓冲机制 |

### 阶段三:手写 Agent Loop(分水岭)
| 文件 | 内容 |
|------|------|
| `13_agent_tool_kimi.py` | 第一次工具调用:tools schema → tool_calls → 结果喂回 |
| `14_agent_loop_kimi.py` | 🎯 完整 Agent Loop:多工具字典分发 + 自主循环 + max_turns |
| `15_agent_chat_kimi.py` | 聊天 × 工具合体:双循环嵌套 |
| `16_agent_chat_stream_kimi.py` | 流式 + 工具:tool_calls 碎片拼装(最硬的一版) |
| `18_classes.py` | Python 类速成(对照 Swift:`__init__`/self/dataclass) |
| `19_agent_class_kimi.py` | Agent 重构为类:状态封装,主程序缩到 5 行 |

### 阶段四:RAG 与记忆
| 文件 | 内容 |
|------|------|
| `17_rag_naive_kimi.py` | RAG 骨架:字面检索(bigram 交集)→ 塞 prompt → 生成 |
| `20_embedding_demo.py` | embedding 初体验:手写余弦相似度,见证语义检索 |
| `21_rag_vector.py` | 🎯 向量 RAG Agent:语义检索 + 工具 + 双模型服务商 |
| `22_persistent_agent.py` | 🎯 当前完全体:+ 跨会话持久记忆(JSON 存档/损坏兜底) |

### 附:Anthropic 格式参考实现
`01_hello_llm.py` / `02_chat_loop.py` / `03_agent_loop.py` —— 同样的概念用 Anthropic
原生 API 的写法(tool_use / stop_reason),与 OpenAI 兼容格式对照用。

## 核心收获

<!-- TODO(你自己写,4-5 条感受最深的。提示可选:大模型无状态、Agent=大脑+手+循环、
     工具保证执行不保证决策、RAG 是模式不是库、prompt 规则要双向测试……用你的话! -->

## 踩坑记录

<!-- TODO(你自己写,挑 5-8 个印象最深的,一行一个:现象 → 原因 → 教训。
     候选:内置名覆盖 list/dict、忘写 return、隐形 self、json.dump 序列化边界、
     写一半崩了污染存档、grounding 规则误伤对话记忆…… -->

## 如何运行

<!-- TODO(你自己写:uv sync 装依赖;.env 需要哪两个 key、分别去哪申请;
     跑 uv run 22_persistent_agent.py) -->

## 下一步计划

- RAG 收尾:文档切块(chunk)、接入 Chroma 向量库、检索质量评估
- 用 LangChain 等框架重写一遍,对照手写版理解框架封装了什么
- MCP(Model Context Protocol)
- 最终作品:一个结合 iOS 背景的差异化 Agent 项目
