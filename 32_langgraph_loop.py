# 🕸️ LangGraph 最小聊天图 —— 把你手写的 while 循环,换成"图"
# 运行:uv run 32_langgraph_loop.py
#
# 目标:先不加工具,让一张 graph 能聊天,摸清 5 个零件:
#   State(MessagesState)=你的 self.messages / Node 节点=调模型那步 /
#   Edge 边=下一步去哪 / START,END=入口出口 / compile→invoke=你的 chat()

import os
import json
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, MessagesState, START, END

load_dotenv()

# ── 脚手架:模型接 Kimi(你写过很多遍的老配方,先给你填好)──
llm = ChatOpenAI(
    model="kimi-k2.6",
    base_url="https://api.moonshot.cn/v1",
    api_key=os.environ.get("MOONSHOT_API_KEY"),
    temperature=1,
)


# ── 该你写①:节点函数 ──
# state 是个字典,state["messages"] 是"当前所有消息"。
# 该把哪个喂给模型?
def chat_node(state):
    reply = llm.invoke(state["messages"])          # TODO(你填):喂 state 里的什么?
    return {"messages": [reply]}      # 返回格式已给好:把回复放进 messages


# ── 该你写②:搭图(这就是本课新概念,核心在这)──
graph = StateGraph(MessagesState)
graph.add_node("chat", chat_node)            # TODO:(节点名字符串, 节点函数)
graph.add_edge(START, "chat")           # TODO:从起点连到你那个节点
graph.add_edge("chat", END)             # TODO:从你那个节点连到终点
app = graph.compile()


# ── 该你写③:跑一次 ──
if __name__ == "__main__":
    result = app.invoke({"messages": [{"role":"user", "content":"你妹子的"}]})   # TODO:塞一条 user 消息 {"role":..,"content":..}
    print(result["messages"][-1].content)                                  # TODO:打印最后一条消息的 .content
