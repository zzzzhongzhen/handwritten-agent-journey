import os
from openai import OpenAI
from dotenv import load_dotenv
import chromadb
import json

load_dotenv()

DOC_FILES = "第2个月复习-AgentLoop.md"
CHUNK_THRESHOLD = 800

sillicon = OpenAI(api_key=os.environ.get("SILICONFLOW_API_KEY"),
                  base_url="https://api.siliconflow.cn/v1")

chroma_client = chromadb.PersistentClient(path="chroma_demo_db")

collection = chroma_client.get_or_create_collection("my_notes", metadata={"hnsw:space": "cosine"})

def embed(text: str) -> list:
    response = sillicon.embeddings.create(model="BAAI/bge-m3", input=text)
    return response.data[0].embedding

def chunk_text():
    with open(DOC_FILES, "r", encoding="utf-8") as f:
        content = f.read()
    result = []
    for chunk in content.split("\n##"):
        parts = chunk.split("\n", maxsplit=1)
        title = parts[0].strip()
        body = parts[1] if len(parts) > 1 else ""
        if len(chunk) > CHUNK_THRESHOLD:
            result.extend(f"{title}\n{para}" for para in body.split("\n\n")
                              if len(para.strip()) > 30)
        else:
            result.append(f"{title}\n{body}")
    return result

def rank_chroma(answer_span, q_vec, collection, n):
    """Chroma:query 要回全部 n 块(已按距离排好)→ 找正确块排第几"""
    result = collection.query(query_embeddings=[q_vec], n_results=n)
    print(f"chroma返回结果：{result}")
    for rank, doc in enumerate(result["documents"][0], start=1):
        if answer_span in doc:
            return rank
    return None

def hit_at(ranks, k):
    return sum(1 for r in ranks if r is not None and r <= k)
def mrr(ranks):
    return sum(1 / r for r in ranks if r is not None) / len(ranks)

if __name__ == "__main__":

    with open("eval_set.json", "r", encoding="utf-8") as f:
        eval_set = json.load(f)
    n = len(eval_set)
    chunk_texts = chunk_text()

    if collection.count() == 0:
        collection.add(
            ids=[f"doc_{i}" for i, _ in enumerate(chunk_texts)],
            embeddings=[embed(text) for text in chunk_texts],
            documents=chunk_texts)
    else:
        print("已从磁盘加载")

    q_vecs = [embed(dic["q"]) for dic in eval_set]

    ranks_ch = [rank_chroma(dic["answer_span"], q, collection, len(chunk_texts)) for q, dic in zip(q_vecs, eval_set)]

    print(f"\n{'Chroma':<12}{f'{hit_at(ranks_ch,1)}/{n}':<10}{f'{hit_at(ranks_ch,3)}/{n}':<10}{mrr(ranks_ch):.3f}")
