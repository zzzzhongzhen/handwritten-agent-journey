# 🧪 合成评估集 + 参数对比实验(封箱版)
# 运行:uv run 25_synthetic_eval.py
#
# 设计要点(都是聊透的):
#   1. LLM 按块出题 + 摘抄"答案句" → 标签锚定原文,不锚定块 → 换切法照样能判分
#   2. 题集生成一次就存盘冻结(eval_set.json)→ 考卷固定,才能公平对比配置
#   3. 同一套题跑多种配置(切块阈值 × top_k)→ 差值决定参数
#
# 注意:这是评估脚本,不是聊天 Agent——所以用普通函数组织,没有类/messages(不需要)。

import os
import json
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

silicon = OpenAI(api_key=os.environ.get("SILICONFLOW_API_KEY"),
                 base_url="https://api.siliconflow.cn/v1")
kimi = OpenAI(api_key=os.environ.get("MOONSHOT_API_KEY"),
              base_url="https://api.moonshot.cn/v1")

DOC_FILE = "第2个月复习-AgentLoop.md"
EVAL_FILE = "eval_set.json"

# ============================================================
# 基础零件(你写过的)
# ============================================================
def embed(text: str) -> list:
    response = silicon.embeddings.create(model="BAAI/bge-m3", input=text)
    return response.data[0].embedding

def cos_sim(a: list, b: list) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = sum(x * x for x in a) ** 0.5
    norm_b = sum(y * y for y in b) ** 0.5
    return dot / (norm_a * norm_b)

def chunk_text(threshold: int) -> list:
    """切块。threshold 成为参数——这就是要调的旋钮之一。"""
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
# 第 1 部分:生成题集(只跑一次,之后从文件加载)
# ============================================================
def generate_one(chunk: str):
    """让 Kimi 出一道题 + 摘抄答案句。返回 (问题, 答案句),失败返回 None。"""
    prompt = f"""你是一个普通用户,刚读了下面这段资料。请提出 1 个这段资料能够回答的问题。

要求:
1. 用口语提问,像真实用户随口问的那样
2. 不要照抄资料里的词汇和标题,换自己的说法
3. 严格输出两行:
   第一行:问题本身(不要引号、不要前缀)
   第二行:资料中能回答该问题的一句原文(必须一字不改地摘抄)

资料:
{chunk}"""
    response = kimi.chat.completions.create(
        model="kimi-k2.6",
        messages=[{"role": "user", "content": prompt}],
    )
    lines = [l.strip() for l in response.choices[0].message.content.strip().split("\n") if l.strip()]
    if len(lines) < 2:
        return None
    return lines[0], lines[1]

def build_eval_set() -> list:
    """按块出题 → 校验答案句真在原文里(质量闸门)→ 存盘冻结。"""
    with open(DOC_FILE, "r", encoding="utf-8") as f:
        full_doc = f.read()

    chunks = chunk_text(800)          # 出题用哪种切法不重要,标签锚定的是原文句子
    eval_set = []
    for i, chunk in enumerate(chunks):
        item = generate_one(chunk)
        if item is None:
            print(f"⚠️ [{i+1}/{len(chunks)}] 输出格式不对,跳过")
            continue
        q, span = item
        if span not in full_doc:      # 质量闸门:模型没有"一字不改"摘抄 → 标签不可信,弃用
            print(f"⚠️ [{i+1}/{len(chunks)}] 答案句不在原文中(模型改写了),跳过: {span[:30]}")
            continue
        print(f"📝 [{i+1}/{len(chunks)}] {q}")
        eval_set.append({"q": q, "answer_span": span})

    with open(EVAL_FILE, "w", encoding="utf-8") as f:
        json.dump(eval_set, f, ensure_ascii=False, indent=2)
    print(f"\n💾 题集已冻结存盘:{EVAL_FILE},共 {len(eval_set)} 题")
    return eval_set

def load_or_build_eval_set() -> list:
    """有存档就加载(冻结原则),没有才生成。"""
    if os.path.exists(EVAL_FILE):
        with open(EVAL_FILE, "r", encoding="utf-8") as f:
            eval_set = json.load(f)
        print(f"📂 加载已冻结的题集:{len(eval_set)} 题(想重新生成就删掉 {EVAL_FILE})")
        return eval_set
    return build_eval_set()

# ============================================================
# 第 2 部分:评估
#   核心思想:先算每道题的"原始事实"——正确块排第几名;
#   一切指标(hit@1/@3/@5、MRR)都从名次列表推导,加指标零成本。
# ============================================================
def get_rank(answer_span: str, q_vec: list, doc_vecs: list):
    """正确块排第几名(1 起)。找不到返回 None。"""
    scored = sorted(((cos_sim(q_vec, vec), doc) for vec, doc in doc_vecs), reverse=True)
    for rank, (_, doc) in enumerate(scored, start=1):
        if answer_span in doc:
            return rank
    return None

def eval_config(eval_set: list, q_vecs: list, doc_vecs: list) -> list:
    """跑整套题,返回每题的名次列表(None = 没检索到)。"""
    return [get_rank(case["answer_span"], q_vec, doc_vecs)
            for case, q_vec in zip(eval_set, q_vecs)]

def hit_at(ranks: list, k: int) -> int:
    """名次 ≤ k 的题数 = hit@k"""
    return sum(1 for r in ranks if r is not None and r <= k)

def mrr(ranks: list) -> float:
    """平均倒数名次:第1名记1、第2名0.5、第3名0.33…… 越高排序越准"""
    return sum(1 / r for r in ranks if r is not None) / len(ranks)

# ============================================================
# 第 3 部分:参数对比矩阵
#   向量预计算原则:问题向量全局算一次;每种切法的块向量算一次;
#   指标(hit@k / MRR)从名次推导,不花任何新算力。
# ============================================================
if __name__ == "__main__":
    eval_set = load_or_build_eval_set()
    n = len(eval_set)

    print("\n⏳ 预计算全部问题的向量(各配置共用,只算一次)...")
    q_vecs = [embed(case["q"]) for case in eval_set]

    print("\n========== 参数对比实验 ==========")
    results = []
    for threshold in (300, 800, 20):
        chunks = chunk_text(threshold)
        print(f"⏳ 阈值={threshold}:{len(chunks)} 块,计算向量中...")
        doc_vecs = [(embed(c), c) for c in chunks]          # 每种切法只算一次
        ranks = eval_config(eval_set, q_vecs, doc_vecs)     # 只算一次名次
        results.append((threshold, hit_at(ranks, 1), hit_at(ranks, 3), mrr(ranks)))

    print(f"\n{'阈值':<8}{'hit@1':<10}{'hit@3':<10}MRR")
    for threshold, h1, h3, m in results:
        print(f"{threshold:<8}{f'{h1}/{n}':<10}{f'{h3}/{n}':<10}{m:.3f}")
    for threshold, top_k, hit1, hitk in results:
        print(f"阈值{threshold:<13} {hit1}/{n:<8} {hitk}/{n}")
