# 🏆 完整 Agent + 流式输出(Kimi 版)
# 运行:uv run 16_agent_chat_stream_kimi.py
#
# 难点:流式下,文字和"工具调用"都是碎片式返回的,要自己拼回来。
# 用一个辅助函数 stream_and_collect 把这块脏活封装掉,主循环保持清爽。

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
# 工具函数 + 注册表 + JSON 描述(和 15 一样)
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

tools = [
    {"type": "function", "function": {
        "name": "calculate", "description": "计算数学表达式并返回精确结果。要算数时用。",
        "parameters": {"type": "object", "properties": {
            "expression": {"type": "string", "description": "如 '28.5 - 26.1'"}}, "required": ["expression"]}}},
    {"type": "function", "function": {
        "name": "get_weather", "description": "查询某个城市的当前温度。要知道天气/温度时用。",
        "parameters": {"type": "object", "properties": {
            "city": {"type": "string", "description": "城市名,如 '北京'"}}, "required": ["city"]}}},
    {"type": "function", "function": {
        "name": "celsius_to_fahrenheit", "description": "把摄氏度换算成华氏度。要做温度换算时用这个,别用 calculate。",
        "parameters": {"type": "object", "properties": {
            "celsius": {"type": "number", "description": "摄氏温度,如 30.1"}}, "required": ["celsius"]}}},
]

def run_tool(name: str, arguments_json: str) -> str:
    func = TOOL_FUNCTIONS.get(name)
    if func is None:
        return f"未知工具 {name}"
    try:
        args = json.loads(arguments_json)
        return str(func(**args))
    except Exception as e:
        return f"工具执行出错: {e}"

# ============================================================
# ⭐ 核心难点封装:消费流式响应
#   - 文字:边收边实时打印(打字机效果)
#   - 工具调用:碎片拼装(名字、参数 JSON 都是一块块来的)
#   返回:(完整文字, 拼好的工具调用列表)
# ============================================================
def stream_and_collect(stream):
    content = ""
    tool_calls = {}          # index -> {"id", "name", "arguments"},按序号归拢碎片
    printed_prefix = False

    for chunk in stream:
        delta = chunk.choices[0].delta

        # ① 文字碎片:实时打印
        if delta.content:
            if not printed_prefix:
                print("🤖 Kimi: ", end="", flush=True)
                printed_prefix = True
            print(delta.content, end="", flush=True)
            content += delta.content

        # ② 工具调用碎片:按 index 归拢,把碎片拼成完整的
        if delta.tool_calls:
            for tcd in delta.tool_calls:
                idx = tcd.index
                if idx not in tool_calls:
                    tool_calls[idx] = {"id": "", "name": "", "arguments": ""}
                if tcd.id:
                    tool_calls[idx]["id"] = tcd.id
                if tcd.function and tcd.function.name:
                    tool_calls[idx]["name"] += tcd.function.name
                if tcd.function and tcd.function.arguments:
                    tool_calls[idx]["arguments"] += tcd.function.arguments   # 参数一段段拼

    if content:
        print()      # 文字流完,换行

    # 字典按序号转成列表
    tool_calls_list = [tool_calls[i] for i in sorted(tool_calls)]
    return content, tool_calls_list

# ============================================================
# 主程序:聊天循环(外) 套 Agent 循环(内),内层用流式
# ============================================================
messages = [{"role": "system", "content": """你是一个友好的助手,可以用工具查天气、算数、换算温度。

规则:
1. 涉及实时天气或温度,必须调用 get_weather 查询,不要凭记忆编造。
2. 涉及温度换算(摄氏↔华氏),必须调用 celsius_to_fahrenheit,绝不自己心算(避免公式记错)。
3. 需要计算时用 calculate,不要口算。
4. 如果工具报错,如实告诉用户哪里出了问题,不要假装成功。
5. 不确定的事就说不知道,不要编造。
6. 回答简洁,用中文。"""}]

print("🏆 完整 Agent(流式版,输入 quit 退出)\n")

while True:
    user_input = input("你: ")
    if user_input.lower() in ("quit", "exit", "退出"):
        print("再见!")
        break

    messages.append({"role": "user", "content": user_input})

    for turn in range(10):
        stream = client.chat.completions.create(
            model="kimi-k2.6", messages=messages, tools=tools, stream=True,
        )
        content, tool_calls = stream_and_collect(stream)

        # 没有工具调用 → 最终答案(已经流式打印过了)→ 存历史,结束这一句
        if not tool_calls:
            messages.append({"role": "assistant", "content": content})
            print()
            break

        # 有工具调用 → 手动拼一条 assistant 消息(带 tool_calls)存历史
        messages.append({
            "role": "assistant",
            "content": content or None,
            "tool_calls": [
                {"id": t["id"], "type": "function",
                 "function": {"name": t["name"], "arguments": t["arguments"]}}
                for t in tool_calls
            ],
        })

        # 执行每个工具,结果塞回
        for t in tool_calls:
            result = run_tool(t["name"], t["arguments"])
            print(f"   🔧 {t['name']}({t['arguments']}) → {result}")
            messages.append({"role": "tool", "tool_call_id": t["id"], "content": result})
