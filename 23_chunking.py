import os
import json
import httpx
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

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
# 2. 余弦相似度:两个向量"方向"有多一致(越近 1 越相似)
#    全是你会的零件:zip 并排遍历、生成器求和、** 0.5 开方
# ============================================================
def cos_sim(a: list, b: list) -> float:
    dot = sum(x * y for x, y in zip(a, b))            # 点积
    norm_a = sum(x * x for x in a) ** 0.5             # a 的长度
    norm_b = sum(y * y for y in b) ** 0.5             # b 的长度
    return dot / (norm_a * norm_b)

HISTORY_FILE = "chat_history.json"

SYSTEM_PROMPT = """你是学习助手,参考资料库是用户的 Agent 开发学习笔记(Agent Loop、工具调用、RAG、Python 等)。
回答时遵守以下规则:
1. 知识类问题:优先依据本次提供的参考资料回答;资料里没有的,如实说"资料里没有这个信息",不要编造。
2. 用户在对话中告诉你的信息(名字、偏好、之前聊过的内容):属于对话记忆,可以正常记住和使用。
3. 需要实时数据(天气、温度)或计算时,使用工具。
4. 以上来源都没有的信息,如实说不知道。"""

class RAGChatAgent:
    """这是一个向量检索增强的agent系统"""
    # ============================================================
    # 1. 把文字变成向量(调 embedding 接口)
    # ============================================================
    def embed(self, text: str) -> list:
        """返回这段文字的语义向量(一个装满小数的列表)"""
        response = self.silicon.embeddings.create(
            model="BAAI/bge-m3",
            input=text,
        )
        return response.data[0].embedding
    

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
        # 实例 1:管聊天(Kimi)
        self.kimi = OpenAI(
            api_key=os.environ.get("MOONSHOT_API_KEY"),
            base_url="https://api.moonshot.cn/v1",
        )
        # 实例 2:管向量检索
        self.silicon = OpenAI(
            api_key=os.environ.get("SILICONFLOW_API_KEY"),
            base_url="https://api.siliconflow.cn/v1",
        )
        self.doc_vecs = self.chunk_text()

    def chunk_text(self) -> list:
        with open("第2个月复习-AgentLoop.md", "r", encoding="utf-8") as f:
            content = f.read()
            split_str = content.split("\n##")
            result = []
            for s_str in split_str:
                parts = s_str.split("\n", 1)
                title = parts[0].strip()           # 标题行
                body = parts[1] if len(parts) > 1 else "" #正文(防某段没有换行,兜一下)
                if len(s_str) > 300:
                    l_chunks = [f"{title}\n{para}" for para in body.split("\n\n") if len(para) > 30]  
                    result.extend(l_chunks)
                else:
                    result.append(f"{title}\n{body}")
            
            doc_vecs = [(self.embed(res), res) for res in result]
            return doc_vecs

    def retrieve(self, user_input) -> str:
        """向量检索,找出最符合用户输入问题的资料"""
        i_vec = self.embed(user_input)
        scored = [(cos_sim(i_vec, d_vec[0]), d_vec[1]) for d_vec in self.doc_vecs]
        scored.sort(key=lambda pair: pair[0], reverse=True)
        for score, doc in scored[:3]:
            print(f"  {score:.4f}  {doc[:30]}...")
        print(f"\n🏆 最相关:{scored[0][1][:30]}...")

        content = "\n\n".join(doc for _, doc in scored[:3])
        return content
    
    def chat(self, user_input) -> str:
        context = self.retrieve(user_input)
        self.messages.append({"role": "user", "content": f"参考资料: \n{context}\n\n我的问题:{user_input}"})
        for turn in range(self.max_turns):
            response = self.kimi.chat.completions.create(
                model="kimi-k2.6",
                messages=self.messages,
                tools=TOOLS_SCHEMA
            )
            msg = response.choices[0].message

            if not msg.tool_calls:
                self.messages.append(msg.model_dump(exclude_none=True))
                self._save(self.messages)
                return msg.content
            
            self.messages.append(msg.model_dump(exclude_none=True))                 # 存"要调工具"这条
            for tc in msg.tool_calls:
                result = self._run_tools(tc)
                print(f"   🔧 {tc.function.name} → {result}")
                self.messages.append({"role": "tool", "tool_call_id": tc.id, "content": result})

        return "(达到最大轮数)"

    def _run_tools(self, tc):
        """执行一个工具"""
        name = tc.function.name
        args = json.loads(tc.function.arguments) 
        func = TOOL_FUNCTIONS.get(name)
        if not func:
            return f"🗜️工具未定义!"
        else:
            try:
                result = func(**args)
            except Exception as e :
                return f"调用工具报错{e}"
            else:
                return result

    def _save(self, data):
        with open(HISTORY_FILE, "w", encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    agent = RAGChatAgent(max_turns=10)
    while True:
        user_input = input("👨🏻：")
        if user_input.lower() in ("quit", "exit", "退出"):
            break
        result = agent.chat(user_input)
        print(f"🤖: {result}\n")