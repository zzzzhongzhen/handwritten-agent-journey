# 第 2 个月复习:手写 Agent Loop(转型分水岭)

> 从"会调大模型聊天"到"会造 Agent"。核心一句话:
> **Agent = 大模型(大脑) + 工具(手) + 循环(反复:请求工具→执行→结果塞回→再问,直到答完)。**

---

## 一、为什么需要 Agent Loop

大模型是"泡在罐子里的大脑":很聪明,但**只能想和说,不能做事**——算不准数、查不了实时信息、碰不到你的文件。
工具调用 = 给大脑装"手":给它一批工具,它需要做事时**请求**调用,你的代码**真执行**,结果喂回去。

---

## 二、messages 多了第四种 role

之前:system / user / assistant。工具调用引入第四种:

| role | 谁说的 |
|------|--------|
| `system` | 你的设定/规则 |
| `user` | 人类 |
| `assistant` | 模型(可能含"要调工具"的请求 tool_calls) |
| **`tool`** | **工具的执行结果**(带 tool_call_id 对应是哪次调用) |

**工具调用本质:还是"往 messages 塞东西让模型看到"**,只是多了 assistant 的 tool_calls 和 tool 结果这两类消息。

---

## 三、加一个工具 = 三步配套

**① 写真正的函数**(你的代码执行)
```python
def get_weather(city: str) -> str:
    ...
    return f"{city}当前温度 {temp}°C"
```

**② 注册进"名字→函数"字典**(分发用)
```python
TOOL_FUNCTIONS = {"get_weather": get_weather, ...}
```

**③ 写 JSON 描述**(给模型看的"说明书")
```python
{"type": "function", "function": {
    "name": "get_weather",                        # 要和注册表 key 一致!
    "description": "查询某城市当前温度。要知道天气时用。",  # 模型靠这决定何时调
    "parameters": {"type": "object",
        "properties": {"city": {"type": "string", "description": "城市名"}},
        "required": ["city"]}}}
```
> 三处 name 必须一致(JSON name = 注册表 key = 逻辑上对应函数)。改名要一起改,否则报"未知工具"。

**JSON Schema 类型用 JSON 词汇**:`string`/`number`/`integer`/`boolean`/`array`/`object`(**没有 float!小数用 number**)。

---

## 四、一轮工具调用的机制

```python
response = client.chat.completions.create(model=..., messages=messages, tools=tools)
msg = response.choices[0].message

if not msg.tool_calls:                 # 模型直接答了
    return msg.content

messages.append(msg)                   # 先存"模型要调工具"这条
for tc in msg.tool_calls:              # 可能一次调多个
    name = tc.function.name
    args = json.loads(tc.function.arguments)   # 参数是 JSON 字符串,要 loads
    result = str(func(**args))                 # **args 通用解包,啥参数都行
    messages.append({"role": "tool", "tool_call_id": tc.id, "content": result})  # 结果塞回
# 再带着结果请求模型 → 拿最终答案
```

---

## 五、Agent Loop = 把"一轮"放进循环

```python
for turn in range(max_turns):          # 心脏循环
    response = ...create(..., tools=tools)
    msg = response.choices[0].message
    if not msg.tool_calls:             # 给最终答案 → 结束
        return msg.content
    # 否则:执行工具,结果塞回,继续循环
    ...
```
- **循环的意义**:一句提问可能要模型来回多次(调工具→看结果→再调或回答)。**删掉循环 → 调完工具没人再问模型,程序直接结束/等下一句,得不到回答。**
- **`max_turns`**:限的是**轮次**(不是工具数!一轮可调多个工具),防无限循环烧钱的保险丝。

---

## 六、多工具分发 = 字典注册表

```python
func = TOOL_FUNCTIONS.get(name)                    # 名字→函数(函数是对象,能存字典)
result = str(func(**args)) if func else f"未知工具 {name}"   # 三元表达式 + 兜底
```
加工具就是"加一行",分发逻辑不用改。

---

## 七、错误处理:把错误喂回给模型(Agent 特有)

```python
try:
    result = str(func(**args))
except Exception as e:
    result = f"工具执行出错: {e}"       # 错误当结果塞回 → 模型看到后可自我修正
```
这里用宽泛 `Exception` 是正当的:目的是"任何工具失败都转成给模型的反馈"。

---

## 八、聊天 + 工具 = 两个循环嵌套

```python
while True:                    # 外层:聊天,接收每句输入
    user_input = input(...)
    messages.append({"role": "user", ...})
    for turn in range(10):     # 内层:Agent 循环,处理这一句(可能多轮工具)
        ...
        if not tool_calls: 打印答案; break   # 答完 → 回外层等下一句
        执行工具、塞回、继续内层
```
一个 messages 装下**一切**:对话历史 + 工具调用 + 工具结果 → 所以它既记得聊过啥、又记得查过啥。

---

## 九、流式 + 工具(代码最难的一版)

- 开 `stream=True` 后,`response` 是块的迭代器,**不能再 `.choices[0].message`**,要 `for chunk in stream` 遍历 `chunk.choices[0].delta`。
- **工具调用也是碎片式返回**:name、arguments(JSON 串)分好几块传来,要**按 index 归拢、把碎片拼回完整**。
- 存历史时要**手动构造** assistant 消息(含 tool_calls),没有现成对象了。
- 框架的核心价值之一,就是把这种脏活封装掉。

---

## 十、关键概念(超越代码的理解)

1. **调哪个工具是模型自己推断的**,不是你写死 if/else。你提供能力,模型负责规划。**范式变了。**
2. **模型怎么决策**:API 把工具描述当文字塞进它的输入;模型靠训练学会的模式,预测出"此刻该输出一个工具调用"。本质仍是"预测下一个 token"。
3. **description(及名字、参数)是模型选工具的依据**:清空一个还能靠其他线索猜;全抹成无意义的才真抓瞎。
4. **可靠性是核心难题**:工具保证"执行准",不保证"决策/公式对"。模型可能记错公式 → 工具精确地算出错误答案。关键运算应把逻辑写死进专用工具,别让模型即兴拼。
5. **system prompt 是控制行为的最强杠杆**:身份、规则、工具使用指引。能提升可靠性,但不是绝对护栏(挡不住提示词注入)。
6. **prompt / system prompt 改不了模型能力上限**(训练固定),只能激发已有能力的发挥。真提升上限:换模型 / 微调 / 给工具·资料(RAG)。

---

## 十一、踩过的坑 / 排查经验

1. JSON Schema 类型填 `float` → 400(用 `number`)。
2. 改工具名只改一处 → "未知工具"(JSON name 必须 = 注册表 key)。
3. 删掉内层循环 → 调完工具不回答、直接等下一句(循环 = 让模型来回处理完)。
4. 错误三来源:编辑器(静态、红线)/ 本地 Python(运行时 Traceback、XxxError)/ 远程服务器(有 HTTP 码如 400,服务器入口校验)。
5. 流式下 `.choices[0].message` 取不到(要遍历 chunk 的 delta)。

---

## 十二、你造出来的东西

- `13_agent_tool_kimi.py` — 单轮工具调用(雏形)
- `14_agent_loop_kimi.py` — 多工具 + 自主循环(手写 Agent Loop 核心)
- `15_agent_chat_kimi.py` — 聊天 + 工具 + 记忆(嵌套循环)
- `16_agent_chat_stream_kimi.py` — 上面 + 流式(最完整)

---

## 自测:合上文档能答吗?

- [ ] messages 里 `tool` 这个 role 装什么?为什么要 tool_call_id?
- [ ] 加一个工具要哪三步?三处 name 什么关系?
- [ ] `for turn in range(max_turns)` 循环删了会怎样?为什么?
- [ ] max_turns 限的是工具数还是轮次?
- [ ] 多工具时怎么知道调哪个函数?字典分发怎么写?
- [ ] 工具报错该怎么处理?为什么这里能用宽泛 Exception?
- [ ] 调哪个工具是谁决定的?它靠什么决定?
- [ ] 为什么"工具算得准"不代表"Agent 答得对"?
- [ ] system prompt 能提升模型能力上限吗?它能干嘛?
- [ ] 聊天+工具为什么要两个循环嵌套?各管什么?

全答得出 = 手写 Agent Loop 真通关。

---

## 下一站:第 3 个月 · RAG + 记忆
给 Agent 外挂"知识"和"长期记忆"——不提升模型本身,而是让它查得到、记得住。本质仍是"往 messages 塞对的东西让模型看到"。
