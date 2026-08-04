# 🎬 第一次工具调用:让大模型"会算数"(Kimi 版)
# 运行:uv run 13_agent_tool_kimi.py
#
# 这是 Agent Loop 的最小雏形:只有一个工具、跑一轮。
# 看懂它,下次我们把它包进 while 循环,就成了完整的 Agent Loop。

import os
import json
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()
client = OpenAI(
    api_key=os.environ.get("MOONSHOT_API_KEY"),
    base_url="https://api.moonshot.cn/v1",
)

# ============================================================
# 第 1 部分:真正的工具函数(你的代码能执行的"手")
# ============================================================
def calculate(expression: str) -> str:
    """计算数学表达式,返回结果字符串。"""
    return str(eval(expression))    # 注:演示用 eval,真实项目别这么写(不安全)

# ============================================================
# 第 2 部分:用 JSON 描述工具,告诉模型"你有这些工具可用"
#   模型不会看到你的函数代码,它只看这段"说明书":
#   工具叫什么、干嘛的、需要什么参数。所以 description 要写清楚!
# ============================================================
tools = [
    {
        "type": "function",
        "function": {
            "name": "calculate",                      # 工具名(要和函数名对上)
            "description": "计算一个数学表达式并返回精确结果。用户要算数时调用它。",
            "parameters": {
                "type": "object",
                "properties": {
                    "expression": {
                        "type": "string",
                        "description": "要计算的数学表达式,例如 '12345 * 6789'",
                    }
                },
                "required": ["expression"],           # expression 是必填的
            },
        },
    }
]

# ============================================================
# 第 3 部分:开始对话
# ============================================================
messages = [
    {"role": "user", "content": "帮我精确计算 12345 乘以 6789 等于多少?"}
]

# ---- 第一次请求:带上工具清单 tools ----
print("① 第一次请求模型(带工具清单)...")
response = client.chat.completions.create(
    model="kimi-k2.6",
    messages=messages,
    tools=tools,               # ← 把工具清单告诉模型
)
msg = response.choices[0].message

# ============================================================
# 第 4 部分:模型是"要调工具"还是"直接回答"?
# ============================================================
if msg.tool_calls:             # 模型决定要调工具
    print("② 模型决定调用工具(它没有直接回答)")

    # 把模型这条"要调工具"的消息加进历史(必须!下一步要对上 id)
    messages.append(msg)

    # 模型可能一次要调多个工具,遍历处理
    for tc in msg.tool_calls:
        name = tc.function.name                       # 要调哪个工具
        args = json.loads(tc.function.arguments)      # 参数(JSON 字符串→dict)
        print(f"   → 模型想调用: {name}({args})")

        # ★ 你的代码真正执行这个工具 ★
        result = calculate(**args)
        print(f"   → 工具真实执行结果: {result}")

        # 把执行结果塞回历史,role 是 "tool",并对上 tool_call_id
        messages.append({
            "role": "tool",
            "tool_call_id": tc.id,
            "content": result,
        })

    # ---- 第二次请求:模型看到工具结果,给出最终回答 ----
    print("③ 把工具结果喂回模型,请它给最终回答...")
    response2 = client.chat.completions.create(
        model="kimi-k2.6",
        messages=messages,
        tools=tools,
    )
    print("\n🤖 最终回答:", response2.choices[0].message.content)

else:                          # 模型觉得不用工具,直接回答了
    print("② 模型直接回答(没调工具):")
    print("🤖", msg.content)
