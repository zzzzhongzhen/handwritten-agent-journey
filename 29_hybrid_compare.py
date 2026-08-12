# ⚔️ 纯向量 vs 纯关键词 vs 混合检索 —— 亲眼看三者差距
# 运行:uv run 29_hybrid_compare.py
#
# 沿用老规矩:手写三种检索,把机制看透(Chroma 也内置了,但 API 还在演进,
#            先懂原理,以后用库时心里有底)。
#
# 三种检索:
#   1. 纯向量(dense) :你手写过的余弦相似度 —— 懂"意思像"(请假↔休假)
#   2. 纯关键词(sparse):字面命中 —— 懂"字对上"(tool_call_id 这种代码符号)
#   3. 混合(hybrid)   :用 RRF 融合两者名次 —— 两个都要
#
# RRF(Reciprocal Rank Fusion,倒数排名融合)= 业界主流融合法:
#   一个文档的融合分 = Σ 1/(K + 它在各方法里的名次)  (K 常取 60)
#   —— 就是你学过的"倒数名次"(MRR 那个)拿来跨方法相加。
#   妙处:只看"名次"不看"原始分",天然绕过"余弦和关键词分数不同量纲"的难题。

import os
import re
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

silicon = OpenAI(api_key=os.environ.get("SILICONFLOW_API_KEY"),
                 base_url="https://api.siliconflow.cn/v1")

DOC_FILE = "第2个月复习-AgentLoop.md"

def embed(text: str) -> list:
    return silicon.embeddings.create(model="BAAI/bge-m3", input=text).data[0].embedding

def cos_sim(a: list, b: list) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    na = sum(x * x for x in a) ** 0.5
    nb = sum(y * y for y in b) ** 0.5
    return dot / (na * nb)

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

# ============================================================
# 关键词:从查询里抓出"英文标识符/代码符号"(≥3 字符),小写化
#   例:"tool_call_id 是啥" → ["tool_call_id"];"怎么请假" → [](中文没有代码符号)
# ============================================================
def keywords(query: str) -> list:
    return [w.lower() for w in re.findall(r"[A-Za-z_][A-Za-z0-9_]{2,}", query)]

# ============================================================
# 三种"排名器":都返回 [块下标, ...],最相关在前
# ============================================================
def dense_ranking(q_vec: list, chunk_vecs: list) -> list:
    """纯向量:按余弦相似度从高到低"""
    return sorted(range(len(chunk_vecs)),
                  key=lambda i: cos_sim(q_vec, chunk_vecs[i]), reverse=True)

def keyword_ranking(kws: list, chunks: list) -> list:
    """纯关键词:数每块命中几个关键词,只保留命中>0 的,按命中数从高到低"""
    scored = [(sum(1 for k in kws if k in chunks[i].lower()), i) for i in range(len(chunks))]
    hit = list(scored)
    hit.sort(reverse=True)                 # 元组先比命中数(你学的字典序)
    return [i for _, i in hit]

def rrf_fusion(rankings: list, K: int = 60) -> list:
    """RRF:把多个名次列表融合成一个。融合分 = Σ 1/(K+名次)"""
    scores = {}
    for ranking in rankings:
        for rank, idx in enumerate(ranking, start=1):
            scores[idx] = scores.get(idx, 0) + 1 / (K + rank)
    return sorted(scores, key=lambda i: scores[i], reverse=True)

def show(title: str, ranking: list, chunks: list, extra=None):
    print(f"  【{title}】")
    if not ranking:
        print("     (无结果)")
        return
    for rank, idx in enumerate(ranking[:3], start=1):
        tag = f"  {extra(idx)}" if extra else ""
        head = chunks[idx].replace("\n", " ")[:34]
        print(f"     #{rank}{tag}  {head}...")

if __name__ == "__main__":
    chunks = chunk_text(800)
    print(f"⏳ {len(chunks)} 块,计算块向量(只算一次)...")
    chunk_vecs = [embed(c) for c in chunks]

    # 两个问题,各自暴露一种检索的强项/软肋
    queries = [
        "怎么防止 agent 陷入死循环一直停不下来",   # 纯语义:靠"意思"找 max_turns,没有精确代码词
        "tool_call_id 这个字段是干嘛的",           # 精确符号:考验字面命中
    ]

    for q in queries:
        print(f"\n{'='*60}\n❓ {q}")
        kws = keywords(q)
        print(f"   抽出的关键词:{kws if kws else '(无英文代码符号)'}\n")

        q_vec = embed(q)
        r_dense = dense_ranking(q_vec, chunk_vecs)
        r_kw = keyword_ranking(kws, chunks)
        print(r_kw)
        r_hybrid = rrf_fusion([r_dense, r_kw])

        show("纯向量", r_dense, chunks,
             extra=lambda i: f"余弦{cos_sim(q_vec, chunk_vecs[i]):.3f}")
        show("纯关键词", r_kw, chunks,
             extra=lambda i: f"命中{sum(1 for k in kws if k in chunks[i].lower())}词")
        show("混合RRF", r_hybrid, chunks)
