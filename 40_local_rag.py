# 🏠 完全本地 RAG —— 本地 embedding + Chroma 重建索引 + 评估验证
# 运行:uv run 40_local_rag.py
#
# 这次多写点核心设计代码(刻意练习):chunk_text、重建索引、评估循环 你来写。
# 卡住可参考你自己的 23/25/28 号(但尽量先凭记忆写)。
# 对照基准(28号云端):hit@1=9/15  hit@3=13/15  MRR=0.734

import json
import chromadb
from openai import OpenAI

# ── 真·样板(给你):本地 embedding ──
ollama = OpenAI(base_url="http://localhost:11434/v1", api_key="ollama")
EMBED_MODEL = "bge-m3:latest"          # 若 ollama list 里名字不同,自己改
def embed(text: str) -> list:
    return ollama.embeddings.create(model=EMBED_MODEL, input=text).data[0].embedding

DOC_FILE = "第2个月复习-AgentLoop.md"
EVAL_FILE = "eval_set.json"


# ══════════════════════════════════════════════════════════
# 该你写①:chunk_text —— 切块(回忆 23/25 号)
#   规格:读 DOC_FILE → 按 "\n##" 切 → 每段取首行作 title、其余作 body
#         若整段 > threshold:按 "\n\n" 拆成段落,每段加 title 前缀,且只留 strip 后 >30 字的
#         否则:整段 "title\nbody" 作为一块
#   返回:一个字符串列表
# ══════════════════════════════════════════════════════════
def chunk_text(threshold: int = 800) -> list:
    with open(DOC_FILE, "r", encoding='utf-8') as f:
        split_str = f.read()
    result = []
    for s_str in split_str.split('\n##'):
        parts = s_str.split("\n", 1)
        title = parts[0].strip()
        body = parts[1] if len(parts) > 1 else ""
        if len(s_str) > threshold:
            chunks = [f"{title}\n{b}" for b in body.split("\n\n") if len(b.strip()) > 30] 
            result.extend(chunks)
        else:
            result.append(f"{title}\n{body}")
    return result


# ══════════════════════════════════════════════════════════
# 该你写②:评估指标(回忆 25/28 号)
#   hit_at(ranks, k):名次 ≤ k 的题数(None 不算)
#   mrr(ranks):平均倒数名次(None 跳过分子,分母是总题数 len(ranks))
# ══════════════════════════════════════════════════════════
def hit_at(ranks: list, k: int) -> int:
    return sum(1 for r in ranks if r is not None and r <= k)

def mrr(ranks: list) -> float:
    return sum(1 / r for r in ranks if r is not None) / len(ranks)

# ══════════════════════════════════════════════════════════
# 该你写③:用 Chroma query 求"正确块排第几名"(回忆 28 号 rank_chroma)
#   规格:query(query_embeddings=[q_vec], n_results=k) → 遍历 result["documents"][0],
#         找到第一个「包含 answer_span」的,返回它的名次(1 起);找不到返回 None
# ══════════════════════════════════════════════════════════
def rank_chroma(answer_span: str, q_vec: list, k: int, col) -> int:
    res = col.query(query_embeddings=[q_vec], n_results=k)
    for rank, chunk in enumerate(res['documents'][0], start=1):
        if answer_span in chunk:
            return rank
    return None


if __name__ == "__main__":
    with open(EVAL_FILE, "r", encoding="utf-8") as f:
        eval_set = json.load(f)
    n = len(eval_set)
    chunks = chunk_text()
    print(f"📂 评估集 {n} 题;{len(chunks)} 块;用本地 embedding 重建 Chroma 索引...")

    # ══════════════════════════════════════════════════════
    # 该你写④:用本地 embedding 重建 Chroma 索引
    #   规格:PersistentClient(path="chroma_db")
    #        → 先删旧 collection "agent_notes_local"(可能不存在,try/except 兜住)
    #        → create_collection(name="agent_notes_local", metadata={"hnsw:space":"cosine"})
    #        → add(ids=每块字符串序号, embeddings=每块的本地向量, documents=chunks)
    # ══════════════════════════════════════════════════════
    client = chromadb.PersistentClient(path="chroma_db")
    collection = client.get_or_create_collection(
        name='agent_notes_local',
        metadata={'hnsw:space': 'cosine'}
    )
    if collection.count()<=0:
        collection.add(
            ids=[f"doc_{i}" for i in range(len(chunks))],
            embeddings=[embed(chunk) for chunk in chunks],
            documents=chunks
        )

    # ══════════════════════════════════════════════════════
    # 该你写⑤:跑评估 + 打印对比
    #   规格:q_vecs = 每题问题的本地向量
    #        ranks = 每题用 rank_chroma 求名次(k 传 len(chunks))
    #        打印 hit@1 / hit@3 / MRR,并和基准 9/15、13/15、0.734 对比
    # ══════════════════════════════════════════════════════
    # TODO 你来写
    ranks = []
    for case in eval_set:
        rank = rank_chroma(case.get('answer_span', ''), embed(case['q']), len(chunks), collection)
        ranks.append(rank)
        print(f"正确块排第几名{rank}")
    print(f"\n{'hit@1':<10}{'hit@3':<10}MRR")

    print(f"\n{f'{hit_at(ranks, 1)}/{n}':<10}{f'{hit_at(ranks, 3)}/{n}':<10}{mrr(ranks):.3f}")
    