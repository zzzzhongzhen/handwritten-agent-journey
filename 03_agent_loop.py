"""
第 2 个月核心:手写 Agent Loop(不依赖任何框架)。

这是整个转型的分水岭。读懂这一个文件,你就懂 agent 的本质了。

agent 的本质就一句话:
  让 LLM 反复【思考 → 调用工具 → 看到结果 → 再思考】,直到任务完成。

运行:
  uv run 03_agent_loop.py

第 2 个月第 1 周先别全懂,重点看:
  (A) 工具怎么定义(TOOLS)
  (B) 工具怎么真正执行(run_tool)
  (C) 那个 while 循环(agent_loop)—— 这是核心中的核心
"""

import json
from anthropic import Anthropic

client = Anthropic()


# ============================================================
# (A) 定义工具:告诉模型"你有哪些能力"
#     每个工具是一段描述 + 参数的 JSON schema。
#     模型读了这些描述,才知道什么时候该调哪个。
# ============================================================
TOOLS = [
    {
        "name": "get_weather",
        "description": "查询某个城市的当前天气",
        "input_schema": {
            "type": "object",
            "properties": {
                "city": {"type": "string", "description": "城市名,比如'北京'"}
            },
            "required": ["city"],
        },
    },
    {
        "name": "calculator",
        "description": "做数学计算,输入一个数学表达式字符串",
        "input_schema": {
            "type": "object",
            "properties": {
                "expression": {"type": "string", "description": "比如 '23 * 17 + 5'"}
            },
            "required": ["expression"],
        },
    },
]


# ============================================================
# (B) 工具的真正实现:这部分是【你的普通代码】,不是 AI。
#     模型只负责"决定调用",真正干活的是这里。
# ============================================================
def run_tool(name: str, tool_input: dict) -> str:
    if name == "get_weather":
        # 真实项目里这里会调天气 API,这里先写死演示
        city = tool_input["city"]
        return f"{city}今天晴,气温 25°C"
    elif name == "calculator":
        # 注意:eval 仅用于学习演示,真实项目别这么用(不安全)
        try:
            return str(eval(tool_input["expression"]))
        except Exception as e:
            return f"计算出错: {e}"
    else:
        return f"未知工具: {name}"


# ============================================================
# (C) Agent Loop —— 核心中的核心。所有框架底层都是这个。
# ============================================================
def agent_loop(user_question: str, max_turns: int = 10):
    # 对话历史(就是第 1 个月学的那个 messages)
    messages = [{"role": "user", "content": user_question}]

    for turn in range(max_turns):  # max_turns 防死循环
        # 1. 把历史 + 工具列表发给模型
        response = client.messages.create(
            model="claude-opus-4-8",
            max_tokens=1024,
            tools=TOOLS,                 # 关键:告诉模型它有这些工具
            messages=messages,
        )

        # 2. 把模型这轮的回复加进历史
        messages.append({"role": "assistant", "content": response.content})

        # 3. 判断:模型是想调工具,还是给出了最终答案?
        if response.stop_reason == "tool_use":
            # 模型决定调用工具。可能一次调多个,逐个执行。
            tool_results = []
            for block in response.content:
                if block.type == "tool_use":
                    print(f"  🔧 调用工具: {block.name}({block.input})")
                    result = run_tool(block.name, block.input)     # 你的代码真正执行
                    print(f"  ↩️  结果: {result}")
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": block.id,    # 用 id 对应是哪次调用
                        "content": result,
                    })
            # 4. 把工具结果喂回模型 —— 它下一轮才能基于结果继续思考
            messages.append({"role": "user", "content": tool_results})
            # 回到循环开头,模型拿着结果继续
        else:
            # 没有要调工具 = 这是最终答案,结束
            final = "".join(b.text for b in response.content if b.type == "text")
            return final

    return "(达到最大轮数,停止)"


# ============================================================
# 试一试。注意第 2 个问题需要 agent 自己分两步:先查天气?不,
# 它需要做计算。你可以换成需要"先查天气再根据温度算点啥"的问题,
# 观察它如何多步调用多个工具。
# ============================================================
if __name__ == "__main__":
    questions = [
        "北京今天天气怎么样?",
        "帮我算一下 1234 * 5678 等于多少",
        "北京天气如何?另外 99 的平方是多少?",  # 这个会触发调用两个工具
    ]
    for q in questions:
        print(f"\n❓ {q}")
        answer = agent_loop(q)
        print(f"✅ {answer}")
