# 🏆 完整 Agent:能连续聊天 + 会用工具 + 有记忆(Kimi 版)
# 运行:uv run 15_agent_chat_kimi.py
#
# 这是你造过的东西的合体:
#   - 聊天循环(while True)     → 能连续对话
#   - Agent 循环(for turn)     → 能连续调工具直到答完
#   - messages 持续累加         → 记得之前聊过啥、查过啥
# 一个 messages 列表装下一切:对话历史 + 工具调用 + 工具结果。

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
# 工具函数
# ============================================================
def calculate(expression: str) -> str:
    return str(eval(expression))

CITIES = {"北京": (39.90, 116.41), "上海": (31.23, 121.47), "深圳": (22.54, 114.06)}

def get_weather(city: str) -> str:
    if city not in CITIES:
        return f"暂不支持城市:{city}"
    lat, lon = CITIES[city]
    r = httpx.get("https://api.open-meteo.com/v1/forecast",
                  params={"latitude": lat, "longitude": lon, "current_weather": True}, timeout=10)
    return f"{city}当前温度 {r.json()['current_weather']['temperature']}°C"

def celsius_to_fahrenheit(celsius: float) -> str:
    return str(celsius * 9 / 5 + 32)

TOOL_FUNCTIONS = {
    "calculate": calculate,
    "get_weather": get_weather,
    "celsius_to_fahrenheit": celsius_to_fahrenheit,
}

# ============================================================
# 工具的 JSON 说明书
# ============================================================
tools = [
    {"type": "function", "function": {
        "name": "calculate",
        "description": "计算数学表达式并返回精确结果。要算数时用。",
        "parameters": {"type": "object", "properties": {
            "expression": {"type": "string", "description": "如 '28.5 - 26.1'"}}, "required": ["expression"]}}},
    {"type": "function", "function": {
        "name": "get_weather",
        "description": "查询某个城市的当前温度。要知道天气/温度时用。",
        "parameters": {"type": "object", "properties": {
            "city": {"type": "string", "description": "城市名,如 '北京'"}}, "required": ["city"]}}},
    {"type": "function", "function": {
        "name": "celsius_to_fahrenheit",
        "description": "把摄氏度换算成华氏度。要做温度换算时用这个,别用 calculate。",
        "parameters": {"type": "object", "properties": {
            "celsius": {"type": "number", "description": "摄氏温度,如 30.1"}}, "required": ["celsius"]}}},
]

# ============================================================
# 执行一个工具(带异常兜底,把错误喂回给模型)
# ============================================================
def run_tool(tc):
    name = tc.function.name
    args = json.loads(tc.function.arguments)
    func = TOOL_FUNCTIONS.get(name)
    if func is None:
        return f"未知工具 {name}"
    try:
        return str(func(**args))
    except Exception as e:
        return f"工具执行出错: {e}"

# ============================================================
# 主程序:聊天循环(外) 套 Agent 循环(内)
# ============================================================
messages = [{"role": "system", "content": """你是一个友好的助手,可以用工具查天气、算数、换算温度。

规则:
1. 涉及实时天气或温度,必须调用 get_weather 查询,不要凭记忆编造。
2. 涉及温度换算(摄氏↔华氏),必须调用 celsius_to_fahrenheit,绝不自己心算(避免公式记错)。
3. 需要计算时用 calculate,不要口算。
4. 如果工具报错,如实告诉用户哪里出了问题,不要假装成功。
5. 不确定的事就说不知道,不要编造。
6. 回答简洁,用中文。"""}]

print("🏆 完整 Agent(输入 quit 退出)\n")

while True:                                   # ===== 外层:聊天循环 =====
    user_input = input("你: ")
    if user_input.lower() in ("quit", "exit", "退出"):
        print("再见!")
        break

    messages.append({"role": "user", "content": user_input})

    for turn in range(10):                    # ===== 内层:Agent 循环 =====
        response = client.chat.completions.create(
            model="kimi-k2.6", 
            messages=messages, 
            tools=tools
        )
        msg = response.choices[0].message

        if not msg.tool_calls:                # 模型给最终答案 → 这一句处理完
            print(f"🤖 Kimi: {msg.content}\n")
            messages.append(msg)              # 把回复存进历史
            break                             # 跳出内层,回外层等下一句

        # 模型要工具 → 执行,把结果塞回,继续内层循环
        messages.append(msg)
        for tc in msg.tool_calls:
            result = run_tool(tc)
            print(f"   🔧 {tc.function.name}({json.loads(tc.function.arguments)}) → {result}")
            messages.append({"role": "tool", "tool_call_id": tc.id, "content": result})
