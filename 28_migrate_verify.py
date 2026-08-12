# ✅ 迁移验证:手写检索 vs Chroma —— 用冻结考卷证明"数字不变 = 迁移成功"
# 运行:uv run 28_migrate_verify.py
#
# 思路(重构安全网):
#   同一套切块、同一批向量、同一份 eval_set,
#   分别用【手写 cos_sim + sort】和【Chroma query】求每道题正确块的名次,
#   再各自算 hit@k / MRR。两边数字应当一致 —— 因为向量一样、都用余弦。
#
# 关键省算力:块向量、问题向量都只算一次;Chroma 直接复用这些向量(不重新 embed)。

import os
import json
import chromadb
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

silicon = OpenAI(api_key=os.environ.get("SILICONFLOW_API_KEY"),
                 base_url="https://api.siliconflow.cn/v1")

DOC_FILE = "第2个月复习-AgentLoop.md"
EVAL_FILE = "eval_set.json"
THRESHOLD = 800

def embed(text: str) -> list:
    return silicon.embeddings.create(model="BAAI/bge-m3", input=text).data[0].embedding

def cos_sim(a: list, b: list) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = sum(x * x for x in a) ** 0.5
    norm_b = sum(y * y for y in b) ** 0.5
    return dot / (norm_a * norm_b)

def chunk_text(threshold: int) -> list:
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

# ---------------- 两种求名次的方式 ----------------
def rank_handwritten(answer_span, q_vec, doc_vecs):
    """手写:跟每块算余弦 → 全排序 → 找正确块排第几(这就是你 25 号的 get_rank)"""
    scored = sorted(((cos_sim(q_vec, vec), doc) for vec, doc in doc_vecs), reverse=True)
    for rank, (_, doc) in enumerate(scored, start=1):
        if answer_span in doc:
            return rank
    return None

def rank_chroma(answer_span, q_vec, collection, n):
    """Chroma:query 要回全部 n 块(已按距离排好)→ 找正确块排第几"""
    result = collection.query(query_embeddings=[q_vec], n_results=n)
    for rank, doc in enumerate(result["documents"][0], start=1):
        if answer_span in doc:
            return rank
    return None

def hit_at(ranks, k):
    return sum(1 for r in ranks if r is not None and r <= k)

def mrr(ranks):
    return sum(1 / r for r in ranks if r is not None) / len(ranks)

if __name__ == "__main__":
    with open(EVAL_FILE, "r", encoding="utf-8") as f:
        eval_set = json.load(f)
    n = len(eval_set)
    print(f"📂 考卷:{n} 题")

    chunks = chunk_text(THRESHOLD)
    print(f"⏳ 切块={len(chunks)} 块,预计算块向量 + 问题向量(只算一次,两法共用)...")
    doc_vecs = [(embed(c), c) for c in chunks]
    q_vecs = [embed(case["q"]) for case in eval_set]

    # Chroma(临时内存库)—— 复用上面算好的向量,不重新 embed
    client = chromadb.EphemeralClient()
    col = client.create_collection("verify", metadata={"hnsw:space": "cosine"})
    col.add(ids=[str(i) for i in range(len(chunks))],
            embeddings=[vec for vec, _ in doc_vecs],
            documents=[doc for _, doc in doc_vecs])

    ranks_hw = [rank_handwritten(c["answer_span"], q, doc_vecs) for c, q in zip(eval_set, q_vecs)]
    ranks_ch = [rank_chroma(c["answer_span"], q, col, len(chunks)) for c, q in zip(eval_set, q_vecs)]

    print(f"\n{'方式':<12}{'hit@1':<10}{'hit@3':<10}MRR")
    print(f"{'手写检索':<11}{f'{hit_at(ranks_hw,1)}/{n}':<10}{f'{hit_at(ranks_hw,3)}/{n}':<10}{mrr(ranks_hw):.3f}")
    print(f"{'Chroma':<12}{f'{hit_at(ranks_ch,1)}/{n}':<10}{f'{hit_at(ranks_ch,3)}/{n}':<10}{mrr(ranks_ch):.3f}")

    same = ranks_hw == ranks_ch
    print(f"\n{'✅ 每题名次完全一致 → 迁移成功' if same else '⚠️ 名次有差异,需要排查'}")
