# 🗄️ RAG Agent —— Chroma 版(23 号的检索层换成 Chroma)
# 运行:uv run 27_agent_chroma.py
#
# 和 23 号比,只换了"检索"这一层:
#   删掉:cos_sim()          → Chroma 内部算,不用我们手写
#   删掉:自己存 doc_vecs    → 存进 Chroma collection,还持久化到磁盘
#   改写:retrieve()         → 一句 collection.query() 代替 手写 cos_sim + sort
# 工具、记忆、持久化、系统提示词 —— 原样保留。

import os
import json
import httpx
import chromadb
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

# ---------------- 工具区(和 23 号完全一样) ----------------
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

# ⛔️ 注意:23 号在这里有个手写的 cos_sim()。Chroma 版删掉了 —— 相似度交给 Chroma 算。

DOC_FILE = "第2个月复习-AgentLoop.md"
HISTORY_FILE = "chat_history.json"
CHUNK_THRESHOLD = 800     # 评估实验跑出来的最优值(你自己发现的:800 附近是甜点)

SYSTEM_PROMPT = """你是学习助手,参考资料库是用户的 Agent 开发学习笔记(Agent Loop、工具调用、RAG、Python 等)。
回答时遵守以下规则:
1. 知识类问题:优先依据本次提供的参考资料回答;资料里没有的,如实说"资料里没有这个信息",不要编造。
2. 用户在对话中告诉你的信息(名字、偏好、之前聊过的内容):属于对话记忆,可以正常记住和使用。
3. 需要实时数据(天气、温度)或计算时,使用工具。
4. 以上来源都没有的信息,如实说不知道。"""


class RAGChatAgent:
    """向量检索增强的 agent —— 检索层用 Chroma"""

    def __init__(self, max_turns):
        if os.path.exists(HISTORY_FILE):
            with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                try:
                    self.messages = json.load(f)
                except json.JSONDecodeError as e:
                    print(f"历史文件已损坏,重新开始: {e}")
                    self.messages = [{"role": "system", "content": SYSTEM_PROMPT}]
        else:
            self.messages = [{"role": "system", "content": SYSTEM_PROMPT}]

        self.max_turns = max_turns
        self.kimi = OpenAI(api_key=os.environ.get("MOONSHOT_API_KEY"),
                           base_url="https://api.moonshot.cn/v1")
        self.silicon = OpenAI(api_key=os.environ.get("SILICONFLOW_API_KEY"),
                              base_url="https://api.siliconflow.cn/v1")

        # 🆕 Chroma:建库(持久化到磁盘)+ 拿一张表(余弦距离)
        self.chroma = chromadb.PersistentClient(path="chroma_db")
        self.collection = self.chroma.get_or_create_collection(
            name="agent_notes", metadata={"hnsw:space": "cosine"})
        self._build_index()

    def embed(self, text: str) -> list:
        response = self.silicon.embeddings.create(model="BAAI/bge-m3", input=text)
        return response.data[0].embedding

    def _chunk_text(self) -> list:
        """只负责切块,返回一串文本(不再自己 embed —— 那步交给建索引)。"""
        with open(DOC_FILE, "r", encoding="utf-8") as f:
            content = f.read()
        result = []
        for s_str in content.split("\n##"):
            parts = s_str.split("\n", 1)
            title = parts[0].strip()
            body = parts[1] if len(parts) > 1 else ""
            if len(s_str) > CHUNK_THRESHOLD:
                result.extend(f"{title}\n{para}" for para in body.split("\n\n")
                              if len(para.strip()) > 30)
            else:
                result.append(f"{title}\n{body}")
        return result

    def _build_index(self):
        """把切块灌进 Chroma。已经建过就跳过(向量持久化在磁盘,不重算、不花钱)。
        ⚠️ 改了笔记 md 后,删掉 chroma_db/ 目录重跑,索引才会更新。"""
        if self.collection.count() > 0:
            print(f"📂 已加载索引:{self.collection.count()} 块(向量已持久化,未重算)")
            return
        chunks = self._chunk_text()
        print(f"🔧 首次建索引:{len(chunks)} 块,计算向量中...")
        self.collection.add(
            ids=[str(i) for i in range(len(chunks))],
            embeddings=[self.embed(c) for c in chunks],
            documents=chunks,
        )
        print(f"✅ 索引就绪:{self.collection.count()} 块")

    def retrieve(self, user_input) -> str:
        """向量检索 —— 一句 query 代替 23 号里手写的 cos_sim 全遍历 + sort。"""
        result = self.collection.query(
            query_embeddings=[self.embed(user_input)],
            n_results=3,
        )
        docs = result["documents"][0]          # 只问 1 个问题 → 取第 0 组
        dists = result["distances"][0]
        for doc, dist in zip(docs, dists):
            print(f"  {1 - dist:.4f}  {doc[:30]}...")   # 余弦距离→相似度,换回熟悉口径
        print(f"\n🏆 最相关:{docs[0][:30]}...")
        return "\n\n".join(docs)

    def chat(self, user_input) -> str:
        context = self.retrieve(user_input)
        self.messages.append({"role": "user", "content": f"参考资料: \n{context}\n\n我的问题:{user_input}"})
        for turn in range(self.max_turns):
            response = self.kimi.chat.completions.create(
                model="kimi-k2.6", messages=self.messages, tools=TOOLS_SCHEMA)
            msg = response.choices[0].message

            if not msg.tool_calls:
                self.messages.append(msg.model_dump(exclude_none=True))
                self._save(self.messages)
                return msg.content

            self.messages.append(msg.model_dump(exclude_none=True))
            for tc in msg.tool_calls:
                result = self._run_tools(tc)
                print(f"   🔧 {tc.function.name} → {result}")
                self.messages.append({"role": "tool", "tool_call_id": tc.id, "content": result})

        return "(达到最大轮数)"

    def _run_tools(self, tc):
        name = tc.function.name
        args = json.loads(tc.function.arguments)
        func = TOOL_FUNCTIONS.get(name)
        if not func:
            return "🗜️工具未定义!"
        try:
            return func(**args)
        except Exception as e:
            return f"调用工具报错{e}"

    def _save(self, data):
        with open(HISTORY_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    agent = RAGChatAgent(max_turns=10)
    while True:
        user_input = input("👨🏻：")
        if user_input.lower() in ("quit", "exit", "退出"):
            break
        result = agent.chat(user_input)
        print(f"🤖: {result}\n")
