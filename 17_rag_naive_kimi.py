# 📚 RAG 最小雏形:朴素关键词检索版(Kimi)
# 运行:uv run 17_rag_naive_kimi.py
#
# 三步:① 从资料库检索相关段落 → ② 塞进 messages → ③ 模型照着回答
# 检索用最笨的"字词重合度"打分——先跑通骨架,下次换真正的向量检索。

import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()
client = OpenAI(
    api_key=os.environ.get("MOONSHOT_API_KEY"),
    base_url="https://api.moonshot.cn/v1",
)

# ============================================================
# 第 1 部分:资料库(模拟你的私有笔记——模型不可能知道这些!)
# 真实场景这些会是读进来的文件,切成一块块(chunk)
# ============================================================
KNOWLEDGE = [
    "服务器信息:团队测试服务器 IP 是 192.168.31.77,SSH 端口 2222,管理员是老王。",
    "请假流程:提前一天在钉钉上提交申请,抄送直属领导,病假需要补交证明。",
    "byron 的学习计划:每周一二晚各2小时、周三四晚各1小时、周末3小时,目标是6个月转型 Agent 工程师。",
    "项目排期:App 3.2 版本 8 月 15 日提审,3.3 版本预计 9 月底,新功能冻结日是每月 1 号。",
    "报销规则:打车费需要行程单,单笔超过 500 元要提前审批,每月 5 号前提交上月报销。",
]

# ============================================================
# 第 2 部分:朴素检索——按"二字组重合度"给每段打分
# 用到你第 1 周学的:集合 set、集合交集 &、列表推导式、sorted
# ============================================================
def bigrams(text: str) -> set:
    """把文本切成所有相邻两个字的组合,如 '服务器' -> {'服务','务器'}"""
    return {text[i:i+2] for i in range(len(text) - 1)}

def retrieve(query: str, top_k: int = 2) -> list:
    """从资料库找出和问题最相关的 top_k 段"""
    q = bigrams(query)
    scored = [(len(q & bigrams(doc)), doc) for doc in KNOWLEDGE]   # 交集大小=重合度
    scored.sort(key=lambda pair: pair[0], reverse=True)            # 按分数从高到低
    return [doc for score, doc in scored[:top_k] if score > 0]     # 取前 k 个(0 分的不要)

# ============================================================
# 第 3 部分:RAG 问答——检索到的资料塞进 messages
# ============================================================
def ask(question: str):
    docs = retrieve(question)
    print(f"🔍 检索到 {len(docs)} 段相关资料:")
    for d in docs:
        print(f"   - {d[:30]}...")

    context = "\n".join(docs) if docs else "(没有找到相关资料)"
    messages = [
        {"role": "system", "content": f"""你是团队助手。只依据下面的参考资料回答问题;
资料里没有的就说"资料里没有这个信息",不要编造。

参考资料:
{context}"""},
        {"role": "user", "content": question},
    ]
    response = client.chat.completions.create(model="kimi-k2.6", messages=messages)
    print(f"🤖 {response.choices[0].message.content}\n")

# ============================================================
# 试试:这些问题模型本身绝不可能知道答案
# ============================================================
if __name__ == "__main__":
    ask("测试服务器的 IP 和端口是多少?")
    ask("我要报销打车费,有什么要求?")
    ask("公司年会是哪天?")            # 资料库里没有 → 看它会不会老实说不知道
    ask("深圳现在什么天气")
