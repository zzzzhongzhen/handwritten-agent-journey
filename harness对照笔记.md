# Harness 源码精读 · 对照笔记

> 精读对象:`03_agent_loop.py`(当初给的参考实现,Anthropic 原生格式)vs 我手写的 `14_agent_loop_kimi.py`(OpenAI/Kimi 格式)。
> 一句话:**同一个 Agent Loop,两套 API 方言;所谓"生产级 harness",内核就是这个 while loop,难的全在外面那圈防护。**

---

## Part 1 · 同一个 loop,两种方言对照

| 环节 | Anthropic(03) | OpenAI / Kimi(14) |
|---|---|---|
| 工具 schema | `{name, description, input_schema}` | `{"type":"function","function":{name, description, parameters}}`(多包一层) |
| 判断要不要调工具 | `response.stop_reason == "tool_use"` | `message.tool_calls` 非空 / `finish_reason=="tool_calls"` |
| 回复结构 | `content` 是**块列表**(text 块 / tool_use 块) | `content` 是**字符串** + 独立 `tool_calls` 字段 |
| 拿参数 | `block.input` —— **已是 dict** ✅ | `tc.function.arguments` —— **JSON 字符串,要 `json.loads`** ⚠️ |
| 调用 id | `block.id` | `tc.id` |
| 喂回结果 | **一条** user 消息,content 装 tool_result 块**列表** | **每工具一条** `role:"tool"` 消息,用 `tool_call_id` 认领 |
| 把 assistant 回复加进历史 | 直接 append `response.content`(整个块列表) | 手动构造 assistant 消息(尤其流式,见 16 号) |

### 三个真正值得记的差异(换供应商 / 面试会踩)

1. **参数解析**:Anthropic 直接给 dict;OpenAI 给**字符串**,忘 `json.loads` 就炸(14 号踩过)。
2. **结果喂回**:Anthropic 多结果**打包进一条** user 消息;OpenAI **一工具一条** `role:"tool"`。换家要整个改写喂回逻辑。
3. **content 模型根本不同**:Anthropic content **天生是块列表**(多模态/多工具原生);OpenAI 是"字符串 + 旁挂 tool_calls"。这决定了两边"加历史"写法不同。

---

## Part 2 · 玩具 loop → 生产级 harness 的差距地图

`03` 只有一个防护:`max_turns`。真实 harness(Codex 那类)在这个内核外还套一圈——**这圈≈JD 的"生产层",也≈M5-6 作品要焊的东西**:

| 防护 | 干什么 | 我学过的钩子 |
|---|---|---|
| 上下文压缩 | 历史太长→摘要/裁剪旧轮次,防 token 爆 | 35 号见过 prompt token 每轮涨 |
| 错误/重试 | 429/503→指数退避+抖动 | 限流那节 |
| 并行工具执行 | 多 tool_use 同时跑,非 for 串行 | — |
| 权限闸门 | 危险工具(删文件/发消息)执行前人确认 | — |
| 成本/预算上限 | 不只轮数,还有 token 预算,超了硬停 | — |
| 可观测 | 结构化日志 / tracing | 35 号雏形 |
| 幂等 | 有副作用的工具重试前要幂等键 | 限流那节 |

**核心认知**:agent harness 的内核 = 手写过的 while loop;工程难度全在外面这圈防护。M5-6 作品 = 把这圈一个个焊上去。
