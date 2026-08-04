# 🏗️ 把 Agent 装进类:ChatAgent(16 号文件的类重构版,非流式)
# 运行:uv run 19_agent_class_kimi.py
#
# 对比 15/16:逻辑一模一样,但 messages、tools、循环全部"住进"了一个对象里。
# 看完你会明白:类 = 把"状态 + 操作状态的函数"打包,主程序变得极简。

import os
import json
import httpx
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

# ============================================================
# 工具函数(和之前一样)
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

TOOLS_SCHEMA = [
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

TOOL_FUNCTIONS = {
    "calculate": calculate,
    "get_weather": get_weather,
    "celsius_to_fahrenheit": celsius_to_fahrenheit,
}

# ============================================================
# ⭐ ChatAgent 类:一个对象装下一个完整的 Agent
# ============================================================
class ChatAgent:

    def __init__(self, system_prompt: str, model: str = "kimi-k2.6", max_turns: int = 10):
        self.client = OpenAI(
            api_key=os.environ.get("MOONSHOT_API_KEY"),
            base_url="https://api.moonshot.cn/v1",
        )
        self.model = model
        self.max_turns = max_turns
        self.messages = [{"role": "system", "content": system_prompt}]   # 状态住在对象里

    def chat(self, user_input: str) -> str:
        """处理用户一句话:内部跑完整的 Agent 循环,返回最终答案。"""
        self.messages.append({"role": "user", "content": user_input})

        for turn in range(self.max_turns):
            response = self.client.chat.completions.create(
                model=self.model,
                messages=self.messages,
                tools=TOOLS_SCHEMA,
            )
            msg = response.choices[0].message

            if not msg.tool_calls:                    # 最终答案
                self.messages.append(msg)
                return msg.content

            self.messages.append(msg)                 # 存"要调工具"这条
            for tc in msg.tool_calls:
                result = self._run_tool(tc)
                print(f"   🔧 {tc.function.name} → {result}")
                self.messages.append({"role": "tool", "tool_call_id": tc.id, "content": result})


        return "(达到最大轮数)"

    def _run_tool(self, tc) -> str:
        """执行一个工具。下划线开头 = 约定的'私有方法'(只在类内部用)。"""
        name = tc.function.name
        args = json.loads(tc.function.arguments)
        func = TOOL_FUNCTIONS.get(name)
        if func is None:
            return f"未知工具 {name}"
        try:
            response = func(**args)
        except Exception as e:
            return f"工具执行出错: {e}"
        else:
            return response

    def history_length(self) -> int:
        return len(self.messages)

# ============================================================
# 主程序:看它变得多干净!
# ============================================================
if __name__ == "__main__":
    agent = ChatAgent("""你是一个友好的助手,可以用工具查天气、算数、换算温度。
涉及实时温度必须用 get_weather 查;温度换算必须用 celsius_to_fahrenheit;不确定就说不知道。回答简洁。""")

    # cat = ChatAgent("你是一只高冷的猫，回答简短爱答不理")
    # print(cat.chat("深圳几度？"))
    # dog = ChatAgent("你是一只狗，每次回答前都汪汪汪")
    # print(dog.chat("深圳几度？"))

    print(f"{(1).__add__(2)}")
    print("🏗️ 类版 Agent(输入 quit 退出)\n")
    while True:
        user_input = input("你: ")
        if user_input.lower() in ("quit", "exit", "退出"):
            break
        answer = agent.chat(user_input)          # ← 一句话,一个方法调用,完事
        print(f"🤖 {answer}\n")
