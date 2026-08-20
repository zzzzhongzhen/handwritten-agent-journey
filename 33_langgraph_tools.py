# 🕸️ LangGraph + 工具 —— 第一次见「条件边」(会分岔的边)
# 运行:uv run 33_langgraph_tools.py
#
# 新概念:图不再是直线,而是会分岔 + 回环:
#   START → chat →(模型要调工具? → tools;不调? → END)
#                  tools → chat(工具做完回到 chat,再让模型接着想)
#   这个"要不要调工具"的分岔,就是你手写的 if msg.tool_calls,在图里叫【条件边】。

import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.tools import tool
from langgraph.graph import StateGraph, MessagesState, START, END
from langgraph.prebuilt import ToolNode

load_dotenv()

# ── 脚手架:三个工具。@tool 让 LangGraph 认识它们;函数的 docstring 就是"给模型看的说明" ──
CITIES = {"北京": (39.90, 116.41), "上海": (31.23, 121.47), "深圳": (22.54, 114.06)}

@tool
def get_weather(city: str) -> str:
    """查询某个城市的当前温度(摄氏度)。要知道天气/温度时用。"""
    import httpx
    if city not in CITIES:
        return f"暂不支持城市:{city}"
    lat, lon = CITIES[city]
    r = httpx.get("https://api.open-meteo.com/v1/forecast",
                  params={"latitude": lat, "longitude": lon, "current_weather": True}, timeout=10)
    return f"{city}当前温度为:{r.json()['current_weather']['temperature']}°C"

@tool
def calculate(expression: str) -> str:
    """计算数学表达式并返回精确结果。要算数时用。"""
    return str(eval(expression))

@tool
def celsius_to_fahrenheit(celsius: float) -> str:
    """把摄氏度换算成华氏度。要做温度换算时用这个,别用 calculate。"""
    return str(celsius * 9 / 5 + 32)

TOOLS = [get_weather, calculate, celsius_to_fahrenheit]

# ── 脚手架:模型 + 绑定工具(bind_tools = 你手写版里的 tools= 参数)──
llm = ChatOpenAI(
    model="kimi-k2.6", 
    base_url="https://api.moonshot.cn/v1",
    api_key=os.environ.get("MOONSHOT_API_KEY"), 
    temperature=1,
    max_retries=5 # 🆕 碰到 429限流 自动退避重试(默认才 2 次,不够)
    )
llm_with_tools = llm.bind_tools(TOOLS)

# ── 脚手架:两个节点 ──
def chat_node(state):
    reply = llm_with_tools.invoke(state["messages"])   # 注意用绑了工具的 llm
    return {"messages": [reply]}

tool_node = ToolNode(TOOLS)   # 预制的"执行工具"节点 = 你手写过的 _run_tools 分发,LangGraph 帮你做好了


# ── 该你写①:路由函数 = 条件边的"大脑" ──
# chat 节点刚产出最后一条消息。看它:模型要不要调工具?
#   要调 → return "tools"(去工具节点)   不调 → return END(结束)
def route(state):
    last = state["messages"][-1]
    if last.tool_calls:                     # TODO(你填):怎么判断"模型这条消息里要求调工具"?(提示:last.tool_calls)
        return "tools"
    return END


# ── 该你写②:搭图(重点:条件边 + 回环)──
graph = StateGraph(MessagesState)
graph.add_node("chat", chat_node)
graph.add_node("tools", tool_node)
graph.add_edge(START, "chat")
graph.add_conditional_edges("chat", route)   # TODO:chat 之后去哪,交给哪个函数决定?
# graph.add_edge("tools", "chat")               # TODO:工具执行完,回到哪个节点继续?
app = graph.compile()


# ── 脚手架:跑一个"要两步工具"的问题 ──
if __name__ == "__main__":
    result = app.invoke({"messages": [{"role": "user", "content": "北京现在几度?换成华氏度是多少?"}]})
    for m in result["messages"]:
        m.pretty_print()        # LangChain 消息的漂亮打印,一条条看清楚
