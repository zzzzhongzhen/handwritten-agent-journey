# 🛰️ LangGraph + tracing(本地回调版)—— 给 agent 装"行车记录仪"
# 运行:uv run 35_langgraph_trace.py
#
# 原理:LangChain 的 callback 机制 —— 你写一个"监听器",
#   它在【每次模型调用】【每次工具调用】发生时被自动通知,你把事件打印出来。
#   这就是最朴素的 tracing:在生命周期挂钩子,记录"谁被调了、花了多少 token、参数是啥"。

import os
import httpx
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.tools import tool
from langchain_core.callbacks import BaseCallbackHandler
from langgraph.graph import StateGraph, MessagesState, START, END
from langgraph.prebuilt import ToolNode

load_dotenv()

# ── 脚手架:工具 + 模型(同 33)──
CITIES = {"北京": (39.90, 116.41), "上海": (31.23, 121.47), "深圳": (22.54, 114.06)}

@tool
def get_weather(city: str) -> str:
    """查询某个城市的当前温度(摄氏度)。要知道天气/温度时用。"""
    if city not in CITIES:
        return f"暂不支持城市:{city}"
    lat, lon = CITIES[city]
    r = httpx.get("https://api.open-meteo.com/v1/forecast",
                  params={"latitude": lat, "longitude": lon, "current_weather": True}, timeout=10)
    return f"{city}当前温度为:{r.json()['current_weather']['temperature']}°C"

@tool
def celsius_to_fahrenheit(celsius: float) -> str:
    """把摄氏度换算成华氏度。要做温度换算时用。"""
    return str(celsius * 9 / 5 + 32)

TOOLS = [get_weather, celsius_to_fahrenheit]

llm = ChatOpenAI(model="kimi-k2.6", base_url="https://api.moonshot.cn/v1",
                 api_key=os.environ.get("MOONSHOT_API_KEY"), temperature=1, max_retries=5)
llm_with_tools = llm.bind_tools(TOOLS)

def chat_node(state):
    return {"messages": [llm_with_tools.invoke(state["messages"])]}

tool_node = ToolNode(TOOLS)

def route(state):
    return "tools" if state["messages"][-1].tool_calls else END

graph = StateGraph(MessagesState)
graph.add_node("chat", chat_node)
graph.add_node("tools", tool_node)
graph.add_edge(START, "chat")
graph.add_conditional_edges("chat", route)
graph.add_edge("tools", "chat")
app = graph.compile()


# ── 脚手架:行车记录仪(新 API,给你写好)──
# 继承 BaseCallbackHandler,重写你关心的"生命周期钩子",事件发生时自动被调用
class TraceCallback(BaseCallbackHandler):
    def __init__(self):
        self.n = 0

    def on_chat_model_start(self, serialized, messages, **kwargs):
        self.n += 1
        print(f"\n🧠 [第{self.n}次模型调用] 喂进 {len(messages[0])} 条消息")

    def on_llm_end(self, response, **kwargs):
        usage = (response.llm_output or {}).get("token_usage")
        if not usage:
            try:
                usage = response.generations[0][0].message.usage_metadata
            except Exception:
                usage = {}
        print(f"   ✅ 模型返回  token 用量: {usage}")

    def on_tool_start(self, serialized, input_str, **kwargs):
        print(f"   🔧 调用工具 {serialized.get('name', '?')}  参数: {input_str}")

    def on_tool_end(self, output, **kwargs):
        print(f"   📤 工具返回: {str(getattr(output, 'content', output))[:60]}")


if __name__ == "__main__":
    question = "北京现在几度?换成华氏度是多少?"
    print(f"❓ {question}")

    # ── 该你写:把行车记录仪挂到这次运行上 ──
    # 提示:invoke 的第二个参数 config={"callbacks": [监听器实例]}
    result = app.invoke(
        {"messages": [{"role": "user", "content": question}]},
        config={"callbacks": [TraceCallback()]},        
    )

    print(f"\n🤖 最终答案:{result['messages'][-1].content}")
