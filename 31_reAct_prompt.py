# 🧠 prompt 版 ReAct —— 不用 function-calling,回到"史前时代"
# 运行:uv run 31_reAct_prompt.py
#
# 和 function-calling 版(15号)的根本区别:
#   ① 不传 tools= —— 模型不知道有"结构化工具通道",只能从 system prompt 的文字里知道有哪些工具
#   ② 模型吐纯文本 "Action: get_weather[北京]" —— 我们自己用正则解析(脆弱!这就是重点体验)
#   ③ 用 stop=["Observation:"] 让模型吐完 Action 就闭嘴,别自己脑补工具结果
#   Observation 由我们执行工具后,当成普通 user 消息拼回去(没有 role:tool 那套)

import os
import re
import httpx
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

# ---------------- 工具:注意 prompt-ReAct 里每个工具只收「一个字符串参数」 ----------------
CITIES = {"北京": (39.90, 116.41), "上海": (31.23, 121.47), "深圳": (22.54, 114.06)}

def get_weather(city: str) -> str:
    if city not in CITIES:
        return f"暂不支持城市:{city}"
    lat, lon = CITIES[city]
    result = httpx.get("https://api.open-meteo.com/v1/forecast",
                       params={"latitude": lat, "longitude": lon, "current_weather": True}, timeout=10)
    return f"{city}当前温度为:{result.json()['current_weather']['temperature']}°C"

def calculate(expression: str) -> str:
    return str(eval(expression))

def celsius_to_fahrenheit(celsius: str) -> str:
    return str(float(celsius) * 9 / 5 + 32)   # 解析出来的是字符串,先转 float

TOOL_FUNCTIONS = {
    "get_weather": get_weather,
    "calculate": calculate,
    "celsius_to_fahrenheit": celsius_to_fahrenheit,
}

# 没有 tools= 了,模型只能从这段「文字」知道有哪些工具、怎么用
SYSTEM_PROMPT = """你是一个会使用工具的助手,必须严格按 ReAct 格式思考,每次只输出【一步】。

格式二选一:

Thought: <你的推理>
Action: <工具名>[<参数>]

或者(当你已经掌握足够信息、能回答时):

Thought: <你的推理>
Answer: <最终答案>

可用工具(只能用这几个,参数放方括号里,只放一个参数):
- get_weather[城市名]           查城市当前温度(摄氏度)。例:get_weather[北京]
- calculate[数学表达式]          计算数学表达式。例:calculate[28.5 - 26.1]
- celsius_to_fahrenheit[摄氏度]  摄氏转华氏。例:celsius_to_fahrenheit[25.3]

规则:
- 一次只输出一个 Thought,后面跟一个 Action 或一个 Answer,然后就停下。
- 绝对不要自己编造 Observation —— 我会执行你的 Action,把真实结果作为「Observation:」告诉你,你再继续下一步。
"""


class ReActAgent:
    def __init__(self, model: str = "kimi-k2.6", max_turns: int = 10):
        self.agent = OpenAI(api_key=os.environ.get("MOONSHOT_API_KEY"),
                            base_url="https://api.moonshot.cn/v1")
        self.model = model
        self.max_turns = max_turns
        self.messages = [{"role": "system", "content": SYSTEM_PROMPT}]

    def chat(self, user_input: str) -> str:
        self.messages.append({"role": "user", "content": user_input})

        for turn in range(self.max_turns):
            # 【新点②】stop=["Observation:"] —— 模型一旦想写 "Observation:" 就被掐断,
            #           逼它吐完 Action 就交回控制权,不许自己瞎编工具结果
            response = self.agent.chat.completions.create(
                model=self.model,
                messages=self.messages,
                stop=["Observation:"]
                # 注意:这里【没有 tools=】—— 这是 prompt-ReAct 和 function-calling 的分水岭
            )
            text = response.choices[0].message.content.strip()
            print(text)                                        # 让你看到 Thought/Action 一步步滚
            self.messages.append({"role": "assistant", "content": text})

            # 模型说能回答了 → 抠出 Answer 返回
            if "Answer:" in text:
                return text.split("Answer:", 1)[1].strip()

            # 【新点③】自己解析文本里的 Action: 工具名[参数]
            action = self._parse_action(text)
            if action is None:
                # 模型格式跑偏了,提醒它一句,再来一轮
                self.messages.append({"role": "user",
                                      "content": "格式不对。请只输出 Action: 工具名[参数] 或 Answer: <答案>"})
                continue

            name, arg = action
            observation = self._run_action(name, arg)
            print(f"Observation: {observation}\n")
            # Observation 当成普通 user 消息拼回去(prompt-ReAct 没有 role:tool)
            self.messages.append({"role": "user", "content": f"Observation: {observation}"})

        return "(已到达最大轮数)"

    def _parse_action(self, text: str):
        """从文本里抠出 (工具名, 参数)。抠不到返回 None。—— 这就是「脆弱的文本解析」本体"""
        m = re.search(r"Action:\s*([A-Za-z_]\w*)\s*\[(.*)\]", text, re.DOTALL)
        if not m:
            return None
        return m.group(1), m.group(2).strip()

    def _run_action(self, name: str, arg: str) -> str:
        func = TOOL_FUNCTIONS.get(name)
        if func is None:
            return f"未知工具:{name}"
        try:
            return func(arg)          # 每个工具只收一个字符串参数
        except Exception as e:
            return f"工具执行出错:{e}"


if __name__ == "__main__":
    agent = ReActAgent()
    while True:
        query = input("你: ")
        if query.lower() in ("exit", "退出", "quit"):
            break
        answer = agent.chat(query)
        print(f"🤖 最终答案:{answer}\n")
