# 🧭 embedding 初体验:亲眼看到"语义距离"(SiliconFlow + bge-m3)
# 前提:.env 里加一行 SILICONFLOW_API_KEY=你的key
# 运行:uv run 20_embedding_demo.py
#
# 目标:用向量相似度,解掉朴素检索(17号)的死穴——
#      "怎么连内网那台机器" 字面上和 "服务器信息" 零重合,但语义应该匹配!

import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

# 还是 openai 库,只换了 base_url 和 key —— "换 API 就是换网址+钥匙"
client = OpenAI(
    api_key=os.environ.get("SILICONFLOW_API_KEY"),
    base_url="https://api.siliconflow.cn/v1",
)

# ============================================================
# 1. 把文字变成向量(调 embedding 接口)
# ============================================================
def embed(text: str) -> list:
    """返回这段文字的语义向量(一个装满小数的列表)"""
    response = client.embeddings.create(
        model="BAAI/bge-m3",
        input=text,
    )
    return response.data[0].embedding

# ============================================================
# 2. 余弦相似度:两个向量"方向"有多一致(越近 1 越相似)
#    全是你会的零件:zip 并排遍历、生成器求和、** 0.5 开方
# ============================================================
def cos_sim(a: list, b: list) -> float:
    dot = sum(x * y for x, y in zip(a, b))            # 点积
    norm_a = sum(x * x for x in a) ** 0.5             # a 的长度
    norm_b = sum(y * y for y in b) ** 0.5             # b 的长度
    return dot / (norm_a * norm_b)

# ============================================================
# 3. 实验:和 17 号一样的资料库
# ============================================================
KNOWLEDGE = [
    "服务器信息:团队测试服务器 IP 是 192.168.31.77,SSH 端口 2222,管理员是老王。",
    "请假流程:提前一天在钉钉上提交申请,抄送直属领导,病假需要补交证明。",
    "byron 的学习计划:每周约 9 小时,目标是 6 个月转型 Agent 工程师。",
    "项目排期:App 3.2 版本 8 月 15 日提审,新功能冻结日是每月 1 号。",
    "报销规则:打车费需要行程单,单笔超过 500 元要提前审批。",
]

if __name__ == "__main__":
    # 朴素检索的死穴问题:字面和"服务器"那条几乎零重合
    query = "我想连到内网那台机器,怎么连?"

    print(f"❓ 问题:{query}\n")
    print("⏳ 正在计算向量(每段文字调一次 embedding 接口)...\n")

    q_vec = embed(query)

    # 先看看向量长什么样
    print(f"向量维度:{len(q_vec)},前 5 个数:{[round(x, 3) for x in q_vec[:5]]}\n")

    # 给每段资料算相似度并排序(和 17 号同一个骨架:算分→绑对→排序)
    scored = [(cos_sim(q_vec, embed(doc)), doc) for doc in KNOWLEDGE]
    scored.sort(key=lambda pair: pair[0], reverse=True)

    print("📊 语义相似度排行:")
    for score, doc in scored:
        print(f"  {score:.4f}  {doc[:30]}...")

    print(f"\n🏆 最相关:{scored[0][1][:40]}...")
    print("👉 对比:17 号的字面匹配对这个问题束手无策;向量检索一击命中。")
