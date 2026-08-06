import os
import json
import httpx
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

# ============================================================
# 2. 余弦相似度:两个向量"方向"有多一致(越近 1 越相似)
#    全是你会的零件:zip 并排遍历、生成器求和、** 0.5 开方
# ============================================================
def cos_sim(a: list, b: list) -> float:
    dot = sum(x * y for x, y in zip(a, b))            # 点积
    norm_a = sum(x * x for x in a) ** 0.5             # a 的长度
    norm_b = sum(y * y for y in b) ** 0.5             # b 的长度
    return dot / (norm_a * norm_b)

SYSTEM_PROMPT = """你是学习助手,参考资料库是用户的 Agent 开发学习笔记(Agent Loop、工具调用、RAG、Python 等)。
回答时遵守以下规则:
1. 知识类问题:优先依据本次提供的参考资料回答;资料里没有的,如实说"资料里没有这个信息",不要编造。
2. 用户在对话中告诉你的信息(名字、偏好、之前聊过的内容):属于对话记忆,可以正常记住和使用。
3. 需要实时数据(天气、温度)或计算时,使用工具。
4. 以上来源都没有的信息,如实说不知道。"""

# ==================================================
# 评估集
# ==================================================
EVAL_SET = [
    {"q": "agent loop作用是什么", "expect": "大脑"},
    {"q": "加一个工具要那几步", "expect": "三步配套"},
    {"q": "json序列化报错怎么回事", "expect": "model_dump"},
    {"q": "工具报错了应该怎么处理", "expect": "错误喂回"},
    {"q": "工具如何调用", "expect": "结果塞回"},
    {"q": "怎么进行流式输出", "expect": "stream"},
    {"q": "工具调用的本质是什么", "expect": "tool_calls"},
    {"q": "我想写一个agent", "expect": "大脑"},
    {"q": "有哪些问题值得注意", "expect": "坑"},
]

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
                if len(s_str) > 800:
                    l_chunks = [f"{title}\n{para}" for para in body.split("\n\n") if len(para) > 30]  
                    result.extend(l_chunks)
                else:
                    result.append(f"{title}\n{body}")
            
            doc_vecs = [(self.embed(res), res) for res in result]
            return doc_vecs
        
    def retrieve3(self, input) -> list:
        i_vec = self.embed(input)
        scored = [(cos_sim(i_vec, d_vec[0]), d_vec[1]) for d_vec in self.doc_vecs]
        scored.sort(key=lambda pair: pair[0], reverse=True)
        return [doc for _, doc in scored[:3]]
    
    def eval(self):
        hit3 = 0
        for case in EVAL_SET:
            docs = self.retrieve3(case["q"])
            if any(case["expect"] in doc for doc in docs):
                hit3 += 1
                print(f"✅ HIT: {case['q']}")                
            else:
                print(f"❌ MISS: {case['q']}, \n期望:{case['expect']} \n检索到:{docs}")
        print(f"hit@3 = {hit3}/{len(EVAL_SET)}")

if __name__ == "__main__":
    agent = RAGChatAgent(max_turns=10)
    agent.eval()