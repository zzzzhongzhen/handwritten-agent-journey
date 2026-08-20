# 🧑‍✈️ Supervisor 多 Agent —— 调度者把任务分派给专精子 agent
# 运行:uv run 36_supervisor.py
#
# 核心洞察:supervisor = 一个"工具 agent",它的"工具"就是别的子 agent。
#   对调度者来说,一个子 agent 和一个工具长得一样 —— 决定调谁、丢任务、收结果。
#   所以这张图 = 你 33 号那张图,只是 tools 换成了"子 agent 们"。
#
#   START → supervisor →(要派活?→ workers=子agent;不派?→ END)
#                ↑                                   │
#                └────────── workers ────────────────┘
#
# ⚠️ RPM 提示:多 Agent 一次任务会连打好几次 Kimi;你账号 RPM=3,可能要等/靠 max_retries。
#            先用"单领域任务"验证路由(调用少),跑通再试双领域。

import os
import httpx
import chromadb
from dotenv import load_dotenv
from openai import OpenAI
from langchain_openai import ChatOpenAI
from langchain_core.tools import tool
from langchain_core.messages import SystemMessage, HumanMessage
from langgraph.graph import StateGraph, MessagesState, START, END
from langgraph.prebuilt import ToolNode

load_dotenv()

# ── 脚手架:共享模型 + embedding + Chroma(你都写过)──
llm = ChatOpenAI(model="kimi-k2.6", base_url="https://api.moonshot.cn/v1",
                 api_key=os.environ.get("MOONSHOT_API_KEY"), temperature=1, max_retries=5)
silicon = OpenAI(api_key=os.environ.get("SILICONFLOW_API_KEY"),
                 base_url="https://api.siliconflow.cn/v1")

def embed(text: str) -> list:
    return silicon.embeddings.create(model="BAAI/bge-m3", input=text).data[0].embedding

chroma = chromadb.PersistentClient(path="chroma_db")
collection = chroma.get_or_create_collection("agent_notes", metadata={"hnsw:space": "cosine"})
# (agent_notes 已在 34 号建好并持久化;这里直接查)

# ══════════════════════════════════════════════════════════════
# 子 agent 1:研究员(RAG,内部 1 次模型调用)—— 脚手架
# ══════════════════════════════════════════════════════════════
def _research(question: str) -> str:
    ctx = "\n\n".join(collection.query(query_embeddings=[embed(question)], n_results=3)["documents"][0])
    resp = llm.invoke([SystemMessage(content=f"你是研究员,只根据以下资料回答问题。\n资料:\n{ctx}"),
                       HumanMessage(content=question)])
    return resp.content

# ══════════════════════════════════════════════════════════════
# 子 agent 2:算数/天气员(一个小工具图 = 你的 33 号)—— 脚手架
# ══════════════════════════════════════════════════════════════
CITIES = {"北京": (39.90, 116.41), "上海": (31.23, 121.47), "深圳": (22.54, 114.06)}

@tool
def get_weather(city: str) -> str:
    """查询某个城市的当前温度(摄氏度)。"""
    if city not in CITIES:
        return f"暂不支持城市:{city}"
    lat, lon = CITIES[city]
    r = httpx.get("https://api.open-meteo.com/v1/forecast",
                  params={"latitude": lat, "longitude": lon, "current_weather": True}, timeout=10)
    return f"{city}当前温度为:{r.json()['current_weather']['temperature']}°C"

@tool
def calculate(expression: str) -> str:
    """计算数学表达式并返回精确结果。"""
    return str(eval(expression))

_wtools = [get_weather, calculate]
_wllm = llm.bind_tools(_wtools)
_wg = StateGraph(MessagesState)
_wg.add_node("chat", lambda s: {"messages": [_wllm.invoke(s["messages"])]})
_wg.add_node("tools", ToolNode(_wtools))
_wg.add_edge(START, "chat")
_wg.add_conditional_edges("chat", lambda s: "tools" if s["messages"][-1].tool_calls else END)
_wg.add_edge("tools", "chat")
_calc_weather_app = _wg.compile()

def _calc_weather(task: str) -> str:
    r = _calc_weather_app.invoke({"messages": [{"role": "user", "content": task}]})
    return r["messages"][-1].content


# ══════════════════════════════════════════════════════════════
# 该你写①:把两个子 agent 包成"工具"(supervisor 的灵魂:子 agent = 工具)
#   docstring 很重要 —— 调度者靠它决定"这个任务派给谁"
# ══════════════════════════════════════════════════════════════
@tool
def research_agent(question: str) -> str:
    """研究员:回答关于 Agent 开发学习笔记的知识问题(如 RAG、Agent Loop、工具调用、Python)。"""
    return _research(question)          # TODO:调用 _research(question)

@tool
def calc_weather_agent(task: str) -> str:
    """计算/天气员:做数学计算、查城市天气或温度换算。"""
    return _calc_weather(task)          # TODO:调用 _calc_weather(task)


# ══════════════════════════════════════════════════════════════
# 该你写②:supervisor = 一个工具 agent,它的"工具"就是两个子 agent
# ══════════════════════════════════════════════════════════════
WORKERS = [research_agent, calc_weather_agent]
supervisor_llm = llm.bind_tools(WORKERS)        # TODO:把 WORKERS 绑给调度者

def supervisor_node(state):
    return {"messages": [supervisor_llm.invoke(state["messages"])]}

def route(state):
    return "workers" if state["messages"][-1].tool_calls else END

graph = StateGraph(MessagesState)
graph.add_node("supervisor", supervisor_node)
graph.add_node("workers", ToolNode(WORKERS))     # "执行工具" = 调对应子 agent
graph.add_edge(START, "supervisor")
graph.add_conditional_edges("supervisor", route)
graph.add_edge("workers", "supervisor")
app = graph.compile()


SUPERVISOR_PROMPT = """你是调度者。你自己不直接回答,而是把任务分派给合适的下属:
- research_agent:回答学习笔记里的知识问题
- calc_weather_agent:算数、查天气、温度换算
一次只派给一个下属,等它返回结果后,再决定要不要派下一个
拿到下属返回的结果后,你综合成最终答案回复用户。"""

if __name__ == "__main__":
    task = "什么是工具调用? 北京今天什么天气"        # 先用单领域任务(调用少,RPM 友好);跑通再换双领域
    print(f"❓ {task}\n")
    result = app.invoke({"messages": [
        {"role": "system", "content": SUPERVISOR_PROMPT},
        {"role": "user", "content": task},
    ]})
    for m in result["messages"]:
        m.pretty_print()
