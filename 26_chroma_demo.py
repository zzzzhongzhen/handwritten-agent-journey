# 🗄️ Chroma 向量数据库 —— 最小闭环 demo
# 运行:uv run 26_chroma_demo.py
#
# 目的:摸清 Chroma 的 4 个核心 API,理解它就是你手写检索的"加速+持久化版"。
#   你手写做过的三件事,Chroma 帮你做:
#     1. 存 (向量, 文本) 对   → 你的 doc_vecs
#     2. 算相似度            → 你的 cos_sim
#     3. 取 top-k            → 你的 sort()[:3]
#
# 关键:Chroma 默认会自己 embedding(小英文模型)。我们不用它的——
#   我们"自带向量"(BGE-m3),让 Chroma 只负责 存/索引/查。
#   这样才能和你的 agent、评估集(都用 BGE-m3)对齐。

import os
import chromadb
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

# 还是你熟悉的 embedding(SiliconFlow / BGE-m3)——向量由我们算,不交给 Chroma
silicon = OpenAI(api_key=os.environ.get("SILICONFLOW_API_KEY"),
                 base_url="https://api.siliconflow.cn/v1")

def embed(text: str) -> list:
    return silicon.embeddings.create(model="BAAI/bge-m3", input=text).data[0].embedding

# 几段假语料(先用简单句子,把 API 看清楚;真数据下一步再接)
DOCS = [
    "请假需要提前一天在钉钉提交申请,由直属领导审批。",
    "公司的服务器部署在阿里云,数据库用的是 PostgreSQL。",
    "报销流程:先在财务系统填单,附上发票,月底统一打款。",
    "新员工入职第一天需要去前台领取门禁卡和工牌。",
    "年会定在每年 12 月的最后一个周五,地点在国际会议中心。",
]

# ============================================================
# API 1:建客户端。PersistentClient = 存到磁盘(重启不丢)
#   对比:chromadb.Client() 是纯内存,进程一结束就没了
# ============================================================
client = chromadb.PersistentClient(path="chroma_db")

# ============================================================
# API 2:拿到一个 collection(≈一张表)
#   metadata 里指定 "cosine" —— 让它用余弦距离,对齐你学的余弦相似度
#   get_or_create:有就拿现成的,没有才建(所以第二次运行不会重复建)
# ============================================================
collection = client.get_or_create_collection(
    name="company_notes",
    metadata={"hnsw:space": "cosine"},   # 默认是 L2 欧氏距离,这里改成余弦
)

# ============================================================
# API 3:add —— 存进去。三样东西一一对应:
#   ids       每条的唯一主键(像数据库主键,自己起)
#   embeddings 我们自己算好的向量(自带,不让 Chroma 算)
#   documents  原文(查出来好还原成文字)
#   幂等保护:已经存过就不再重复 add(演示"持久化"——第二次运行会走这里)
# ============================================================
if collection.count() == 0:
    print("🔧 首次运行:计算向量并写入 Chroma...")
    collection.add(
        ids=[f"doc_{i}" for i in range(len(DOCS))],
        embeddings=[embed(d) for d in DOCS],
        documents=DOCS,
    )
else:
    print(f"📂 已从磁盘加载,collection 里已有 {collection.count()} 条(向量没重算,省钱)")

print(f"✅ 当前 collection 共 {collection.count()} 条\n")

# ============================================================
# API 4:query —— 查。给问题向量,要 top-k
#   query 内部就是你手写的:跟每条算余弦 → 排序 → 取前 k
#   返回的 distances 是"余弦距离"= 1 - 余弦相似度(越小越近)
# ============================================================
question = "怎么请假?"
question2 = "服务器在哪?"
print(f"❓ 问题:{question}\n")
print(f"❓ 问题:{question2}\n")

result = collection.query(
    query_embeddings=[embed(question), embed(question2)],
    n_results=3,
)

for docs, dists in zip(result["documents"], result["distances"]): 
    for rank, (doc, dist) in enumerate(zip(docs, dists), start=1):
        similarity = 1 - dist                       # 距离→相似度,换回你熟悉的口径
        print(f"  #{rank}  相似度 {similarity:.4f}  {doc}")
