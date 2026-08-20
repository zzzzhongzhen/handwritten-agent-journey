# 🕸️ LangGraph + RAG —— 把"检索"做成图里的一个节点
# 运行:uv run 34_langgraph_rag.py
#
# 新概念只有一个:检索(retrieve)也是一个节点,放在 chat 前面先跑。
#   START → retrieve → chat →(要工具?→ tools;不要?→ END)
#                       ↑                          │
#                       └──────── tools ───────────┘
#   retrieve 只在开头跑一次:读用户问题 → 查 Chroma → 把资料塞进 messages 给 chat 看。

import os
import httpx
import chromadb
from dotenv import load_dotenv
from openai import OpenAI
from langchain_openai import ChatOpenAI
from langchain_core.tools import tool
from langchain_core.messages import SystemMessage
from langchain_core.messages import HumanMessage
from langgraph.graph import StateGraph, MessagesState, START, END
from langgraph.prebuilt import ToolNode

load_dotenv()

# ── 脚手架:embedding + Chroma(全是你 27/28 写过的,直接给你)──
silicon = OpenAI(api_key=os.environ.get("SILICONFLOW_API_KEY"),
                 base_url="https://api.siliconflow.cn/v1")

def embed(text: str) -> list:
    return silicon.embeddings.create(model="BAAI/bge-m3", input=text).data[0].embedding

DOC_FILE = "第2个月复习-AgentLoop.md"

def chunk_text(threshold: int = 800) -> list:
    with open(DOC_FILE, "r", encoding="utf-8") as f:
        content = f.read()
    result = []
    for s_str in content.split("\n##"):
        parts = s_str.split("\n", 1)
        title = parts[0].strip()
        body = parts[1] if len(parts) > 1 else ""
        if len(s_str) > threshold:
            result.extend(f"{title}\n{para}" for para in body.split("\n\n")
                          if len(para.strip()) > 30)
        else:
            result.append(f"{title}\n{body}")
    return result

chroma = chromadb.PersistentClient(path="chroma_db")
collection = chroma.get_or_create_collection("agent_notes", metadata={"hnsw:space": "cosine"})
if collection.count() == 0:
    chunks = chunk_text()
    print(f"🔧 首次建索引:{len(chunks)} 块...")
    collection.add(ids=[str(i) for i in range(len(chunks))],
                   embeddings=[embed(c) for c in chunks], documents=chunks)

# ── 脚手架:工具 + 模型(33 号那套,直接给你)──
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
def calculate(expression: str) -> str:
    """计算数学表达式并返回精确结果。要算数时用。"""
    return str(eval(expression))

TOOLS = [get_weather, calculate]

llm = ChatOpenAI(model="kimi-k2.6", base_url="https://api.moonshot.cn/v1",
                 api_key=os.environ.get("MOONSHOT_API_KEY"), temperature=1, max_retries=5)
llm_with_tools = llm.bind_tools(TOOLS)


# ── 该你写①:检索节点(本课新概念)──
# 读用户问题 → 查 Chroma 取最相关的 3 块 → 拼成一段资料 → 作为 SystemMessage 塞回去
def retrieve_node(state):
    question = state["messages"][-1].content         
    result = collection.query(query_embeddings=[embed(question)], n_results=3)
    context = "\n\n".join(result["documents"][0])                        # TODO:把 result["documents"][0](3 段文字)用 "\n\n" 拼成一段
    print(f"🔍 检索到 3 块,最相关:{result['documents'][0][0][:30]}...")
    return {"messages": [SystemMessage(content=f"参考资料:\n{context}")]}


# ── 脚手架:聊天/工具节点 + 路由(同 33,直接给你)──
def chat_node(state):
    return {"messages": [llm_with_tools.invoke(state["messages"])]}

tool_node = ToolNode(TOOLS)

def route(state):
    return "tools" if state["messages"][-1].tool_calls else END


# ── 该你写②:搭图(新:retrieve 要排在最前面)──
graph = StateGraph(MessagesState)
graph.add_node("retrieve", retrieve_node)
graph.add_node("chat", chat_node)
graph.add_node("tools", tool_node)
graph.add_edge(START, "retrieve")          
graph.add_edge("retrieve", "chat")           
graph.add_conditional_edges("chat", route)
graph.add_edge("tools", "chat")
app = graph.compile()


if __name__ == "__main__":
    result = app.invoke({"messages": [HumanMessage(content="什么是工具调用?")]}) # 
    for m in result["messages"]:
        m.pretty_print()
