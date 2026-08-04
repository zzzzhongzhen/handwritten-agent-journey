# 🔁 完整的 Agent Loop:多工具 + 自主循环(Kimi 版)
# 运行:uv run 14_agent_loop_kimi.py
#
# 这是 Agent 的心脏:模型自己决定调哪些工具、调几次,直到能回答为止。
# 你会看到它为了回答一个问题,自主地连续调用多个工具。

import os
import json
import httpx
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()
client = OpenAI(
    api_key=os.environ.get("MOONSHOT_API_KEY"),
    base_url="https://api.moonshot.cn/v1",
)

# ============================================================
# 第 1 部分:工具函数(真正能执行的"手")
# ============================================================
def calculate(expression: str) -> str:
    """计算数学表达式。"""
    return str(eval(expression))     # 演示用,真实项目别用 eval

def celsius_to_fahrenheit(celsius: float) -> str:
    """摄氏度转成华氏度"""
    F = celsius * 9/5 + 32
    return str(F)

CITIES = {"北京": (39.90, 116.41), "上海": (31.23, 121.47), "深圳": (22.54, 114.06)}

def get_weather(city: str) -> str:
    """查某城市当前温度(复用你之前学的 Open-Meteo 天气 API)。"""
    if city not in CITIES:
        return f"暂不支持城市:{city}"
    lat, lon = CITIES[city]
    r = httpx.get(
        "https://api.open-meteo.com/v1/forecast",
        params={"latitude": lat, "longitude": lon, "current_weather": True},
        timeout=10,
    )
    temp = r.json()["current_weather"]["temperature"]
    return f"{city}当前温度 {temp}°C"

# ============================================================
# 第 2 部分:工具注册表(名字 → 函数),分发时用
# ============================================================
TOOL_FUNCTIONS = {
    "calculate": calculate,
    "get_weather": get_weather,
    "celsius_to_fahrenheit": celsius_to_fahrenheit
}

# ============================================================
# 第 3 部分:工具的 JSON 说明书(给模型看的)
# ============================================================
tools = [
    {
        "type": "function",
        "function": {
            "name": "calculate",
            "description": "计算数学表达式并返回精确结果。要算数时用。",
            "parameters": {
                "type": "object",
                "properties": {
                    "expression": {"type": "string", "description": "如 '28.5 - 26.1'"},
                },
                "required": ["expression"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_weather",
            "description": "查询某个城市的当前温度。要知道天气/温度时用。",
            "parameters": {
                "type": "object",
                "properties": {
                    "city": {"type": "string", "description": "城市名,如 '北京'"},
                },
                "required": ["city"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "celsius_to_fahrenheit",
            "description": "将摄氏度转成华氏度",
            "parameters": {
                "type": "object",
                "properties": {
                    "celsius": {"type": "number", "description": "如 '30.1'"},
                },
                "required": ["celsius"],
            },
        },
    }
]

# ============================================================
# 第 4 部分:Agent Loop —— 心脏
# ============================================================
def agent_loop(user_question: str, max_turns: int = 10) -> str:
    messages = [
        {"role": "system", "content": "你是一个助手,可以用工具查天气、算数。"},
        {"role": "user", "content": user_question},
    ]

    for turn in range(max_turns):          # 最多循环 max_turns 次(保险)
        print(f"\n===== 第 {turn + 1} 轮 =====")
        response = client.chat.completions.create(
            model="kimi-k2.6",
            messages=messages,
            tools=tools,
        )
        msg = response.choices[0].message

        # 情况 A:模型没要工具 → 它能直接回答了 → 结束
        if not msg.tool_calls:
            print("模型给出最终答案,循环结束 ✅")
            return msg.content

        # 情况 B:模型要调工具 → 执行,把结果塞回,继续循环
        messages.append(msg)               # 先把模型"要调工具"这条存进历史
        for tc in msg.tool_calls:
            name = tc.function.name
            args = json.loads(tc.function.arguments)

            func = TOOL_FUNCTIONS.get(name)                    # 按名字找函数
            if func is None:
                result = f"未知工具{name}"
            else:
                try:
                    result = str(func(**args))
                except Exception as e:
                    result = f"工具执行出错{e}"
            print(f"🔧 调用 {name}({args}) → {result}")

            messages.append({                                  # 结果塞回历史
                "role": "tool",
                "tool_call_id": tc.id,
                "content": result,
            })
        # for 结束,回到 for turn 顶部,带着工具结果再问模型

    return "(达到最大轮数,没能得出结论)"

# ============================================================
# 第 5 部分:试一个"需要连续调多个工具"的问题
# ============================================================
if __name__ == "__main__":
    question = "深圳现在几度？换算成华氏度是多少？"
    print(f"❓ 问题:{question}")
    answer = agent_loop(question)
    print(f"\n🤖 最终回答:\n{answer}")
