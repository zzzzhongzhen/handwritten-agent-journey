# Agent 工程 · 面试速记

> 覆盖 01~43 号全程(手写 Agent Loop → RAG → 评估 → 框架/MCP → 本地部署)。
> 和 `原理Tier1-面试速记.md`(LLM 原理)配套 = 完整面试弹药库。
> 规矩:以后做项目遇到的重要流程/概念/生产坑,继续往这两份里加。

---

## Part A · Agent 核心原理与流程

- **LLM 无状态**:模型不记得上一句,对话历史全靠自己维护 `messages`(user + assistant 都要 append)。这是 Agent 的地基。
- **messages 三角色**:system(设定)/ user(用户)/ assistant(模型)。工具结果单列一类(Anthropic 用 user 装 tool_result 块 / OpenAI 用 `role:"tool"`)。
- **Agent Loop 本质一句话**:让 LLM 反复【思考 → 调工具 → 看结果 → 再思考】,直到收尾。所有框架底层都是这个 while 循环。
- **工具调用机制**:模型**只看 tool 的 JSON 描述(尤其 description),看不到函数代码**。它决定"调哪个、传什么参";真正执行是你的普通代码。
- **ReAct**:Thought/Action/Observation 循环;prompt-based 版靠 `stop=["Observation:"]` + 正则解析,"Observation:" 是自定义约定不是模型内建。
- **Agent 核心软肋**:工具保证**执行准**,不保证模型**决策/公式对**。关键运算要把逻辑**写死进专用工具**,别让模型现编。
- **错误自愈不可靠**:工具失败后模型有时能自己算对(如华氏度),但不可信,别指望。

---

## Part B · RAG 与检索

- **RAG 是架构模式不是库**(类比 MVC):检索相关资料 → 塞进 prompt → 模型据此答。
- **embedding + 余弦相似度**:文本转向量,余弦只看方向(夹角),解决"字面不重合但语义相同"(字面匹配的死穴)。
- **chunk 切块**:为什么切(段落太大稀释语义/超上下文)、标题前缀=给每块加上下文块头、段落级过滤放在**数据产生层**。
- **向量库**:暴力遍历 → ANN/HNSW("跳着找",不逐个比)。**Chroma 默认 query = 纯向量余弦**(它自称"检索引擎",也支持 sparse/hybrid/元数据过滤/多模态,但默认只跑 dense)。
- **混合检索**:dense(懂语义)/ sparse(懂字面符号)/ **RRF 融合**(Σ 1/(K+rank),只比名次躲量纲不匹配)。**实测教训:强 embedder + 小语料下,纯向量已够,hybrid 反添噪声 → 别信二手结论,要用评估集实测。**
- **grounding 会误伤对话记忆**:"只依据参考资料"会导致模型不记用户名字 → 按**信息来源分治**的 system prompt(资料归资料、对话归对话)。这是可讲的真实案例。
- **知识 vs 行为**:新知识用 **RAG**(外挂),不是微调(微调改行为不加知识)。两者互补。

---

## Part C · 评估(可观测的地基)

- **指标**:hit@k(命中前 k)、MRR(平均倒数名次)、多块答案换 **Recall@k**(检索负责召回全、LLM 负责合)。
- **answer_span 锚定原文**:标签锚在"答案句"而非"第几块",**解耦切块方式**(改切法不用重标)。
- **质量闸门**:合成评估里 span 必须在原文能找到(22 块出 15 题,过滤掉幻觉题)。
- **冻结测试集**:考卷 json 存下来别动,才能横向比参数。
- **评估集四来源**:线上日志 / LLM 合成 / 坏案例 / 二八高频。
- **方法论金句**:**差值是调参的尺**(200/300 数字全同=参数平台期;top1→top3 +4 题=排序不准的定量证据)。
- **改参数必须回归测试**;长任务必须打印进度。

---

## Part D · 生产层(JD 缺口 · 大项目要焊的防护圈)

> 核心认知:**生产级 harness 内核=手写过的 while loop,难度全在外面这圈防护。M5-6 作品=把这圈一个个焊上去。**

- **多 Agent 编排**:supervisor 三模式 —— ①工具型(子 agent 包成 @tool)②节点型 supervisor ③交接型 swarm。判据 = 控制权还给谁 + 要不要共享上下文。路由靠工具调用。
- **可观测 / tracing**:callback hooks(on_llm_start/end、on_tool_start/end);**prompt token 每轮涨(历史累加 + 工具 schema 重发)= 烧钱根源**。
- **限流**:RPM vs 并发是**两把不同的锁**;429(限流)vs 503(服务不可用);**瞬时错误才重试**,永久错误(400/401)别重试。
- **重试**:指数退避 + **抖动 jitter**(防惊群 thundering herd);尊重 `Retry-After`。
- **幂等**:有副作用的动作(发消息/建单)重试前要**幂等键**,否则重复执行。
- **上下文压缩**:历史太长 → 摘要 / 裁剪旧轮次(防 token 爆 + 控成本)。
- **成本优化**:prompt caching、模型路由(简单任务走小模型)。
- **安全护栏**:prompt injection、OWASP LLM Top 10、危险工具执行前人工确认(权限闸门)。
- **服务化**:FastAPI + async(并发处理请求)。
- **预算上限**:不只限轮数,还要限 token 预算 / 成本,超了硬停。

---

## Part E · 框架与协议

- **LangChain(零件库:ChatOpenAI/@tool/messages)vs LangGraph(编排层:图/状态/循环)**。
- **LangGraph**:StateGraph、节点、边、条件边(add_conditional_edges)、START/END、ToolNode、compile/invoke。**MessagesState 靠 reducer 自动累加**。graph.invoke 吃**状态** `{"messages":[...]}`,llm.invoke 吃**消息列表**——别混。
- **MCP(Model Context Protocol)**:
  - 是**协议**(mcp 库=实现);底层 **JSON-RPC 2.0**;跟传输方式无关。
  - **三原语**:Tools(工具)/ Resources(数据)/ Prompts(提示模板)。
  - **transport**:stdio(本地,进程用标准输入输出当管道,主流)vs HTTP/SSE(远程多客户端);本地↔远程只换 transport。
  - **"Context" = 模型需要的外部一切**,不是只指上下文窗口文字。
  - 握手要版本协商;工具的 inputSchema 由函数签名自动生成;跨进程 tools/call。
- **本地部署**:Ollama(运行器)/ 模型(Qwen 等)/ openai(客户端)**三层**;只改 base_url/api_key/model 就切本地。**量化**(4bit 压缩,GGUF);OpenAI 兼容 API。**模型不自省运行时**(问它跑在本地还是云会瞎答=幻觉,要写进 system prompt)。本地 7B "够用不顶尖"。**量化有真实代价**:用评估集量出 hit@1/MRR 小降(13/15 持平、MRR 0.734→0.701)。

---

## Part F · 生产级坑(真实踩过的 bug —— "讲个你调过的 bug")

> 这些是行为面 + 技术面的金矿,每条都能展开讲"现象→定位→根因→修复"。

- **序列化边界**:`ChatCompletionMessage` 不能直接 `json.dump` → 先 `model_dump(exclude_none=True)`。理解"对象 ↔ 可存储格式"的边界。
- **原子写入**:存档写一半程序崩 → 文件损坏(JSONDecodeError)→ 写临时文件再 rename(原子替换)。
- **忘写 return**(值没交出去):祖传高频坑,Swift 单表达式隐式返回的习惯迁移。
- **内置名当变量/参数名**(`list`/`dict`):踩过多次,要盯。
- **OpenAI arguments 是 JSON 字符串**,忘 `json.loads` 就炸(Anthropic 直接给 dict)。
- **JSON Schema 没 float**,数字类型用 `number`(写 float 报 400)。
- **短路求值顺序**:`r <= k and r is not None` 会 TypeError(None 先比大小)→ 守卫放前面 `r is not None and r <= k`。
- **改函数返回契约会污染下游**:keyword_ranking 从"返回 top-k"改成"全返回",污染了 RRF 结果。改契约要查所有调用方。
- **兜底 except 忘赋值**(兜底自己没兜住,变量未定义又抛)。
- **错误三来源**:编辑器静态检查 / 本地 Python 运行时 / 远程服务器 HTTP 码(400 是服务器入口校验,模型没参与)。分清报错来自哪一层。
- **密钥安全**:key 只进环境变量 / .env(加 .gitignore),**不进代码/截图/聊天**;.zshrc 明文存 token 是隐患。
- **Git**:commit -m 少空格会导致 commit 没发生(看命令输出);提交署名走对的邮箱;HTTPS vs SSH 凭证链。

---

## Part G · 高频面试题速答(工程版)

- **什么是 Agent?** LLM + 工具 + 循环:模型反复思考→调工具→看结果→再思考直到收尾。
- **LLM 是无状态的,怎么实现多轮记忆?** 自己维护 messages,每轮把 user 和 assistant 都 append 回去,整个历史重新发给模型。
- **工具调用怎么工作?** 给模型一份工具的 JSON schema(名字/描述/参数),模型只读描述决定调哪个传什么,你的代码执行后把结果塞回 messages 再问模型。
- **RAG 解决什么问题?** 给模型外挂知识(它没训练过的/私有的),检索相关片段塞进 prompt,减少幻觉。
- **怎么评估检索质量?** hit@k / MRR / Recall@k + answer_span 锚定 + 冻结测试集;靠指标差值调参。
- **多 Agent 怎么编排?** supervisor 路由(子 agent 当工具 / 节点 / 交接);按"控制权给谁+要不要共享上下文"选模式。
- **怎么做限流和重试?** 区分瞬时(429/503,重试)vs 永久(400,不重试);指数退避+抖动;有副作用的动作加幂等键。
- **MCP 是什么?** 让工具/数据以标准协议(JSON-RPC)暴露,任何客户端可发现调用;工具从"焊在某 agent 里"变成"谁都能连的服务"。
- **LangChain 和 LangGraph 区别?** 前者是零件库,后者是编排层(图/状态/循环/条件边)。
- **讲个你调过的 bug?** → 见 Part F,任选(序列化边界 / 原子写入 / RRF 被返回契约污染,都能讲出根因)。
