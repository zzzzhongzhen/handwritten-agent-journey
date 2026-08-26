# 🧠 Attention 手算 —— 从你 RAG 里手写的 cosine 检索,推导出 Transformer 的核心
# 运行:.venv/bin/python 41_attention_by_hand.py
#
# 大跨越:你在 24/28 号手写过 cosine 检索 —— "query 跟每个 chunk 算相似度,谁像取谁"。
# Attention 就是这套东西搬进模型内部:每个词(token)轮流当一次 query,
# 去跟句子里所有词算"相似度",再按相似度【加权融合】它们的信息,得到自己的新表示。
# 区别只在:RAG 是"一个 query 对一堆文档";self-attention 是"每个词同时对所有词"。

import numpy as np
np.set_printoptions(precision=3, suppress=True)

# ── 样板(给你):一句话 4 个词,每个词先变成向量(embedding)──
# 手捏 dim=4 的小向量,方便你像手算 RRF 那样验证。刻意让语义相关的词向量靠近:
tokens = ["猫", "追", "老鼠", "跑"]
X = np.array([
    [1.0, 0.0, 1.0, 0.0],   # 猫   ┐ 这俩向量很像(都在"名词/主体"方向)
    [0.0, 1.0, 0.0, 1.0],   # 追   ┐ 这俩很像(都在"动作"方向)
    [1.0, 0.0, 0.9, 0.1],   # 老鼠 ┘ 跟"猫"像
    [0.0, 0.9, 0.1, 1.0],   # 跑   ┘ 跟"追"像
])

# 最简版 self-attention:先不引入"可学习的投影矩阵",直接令 Q=K=V=X。
# (Q=我在找什么 / K=我能被搜到的标签 / V=我真正携带的信息;真模型里它们是 X 各乘一个学出来的矩阵,
#  概念先放一放,今天只抓"相似度加权融合"这个灵魂。)
Q = K = V = X


# ══════════════════════════════════════════════════════════
# 该你写①:softmax —— 把一行"原始分数"变成"加起来=1 的权重"
#   这就是你在 RAG 里"归一化相似度"的严格版。数学:softmax(z)_i = e^{z_i} / Σ_j e^{z_j}
#   规格:scores 是 (n, n) 矩阵,对【每一行】各自做 softmax(axis=1),返回同形状矩阵。
#   数值稳定小技巧:先减去每行最大值再取 exp(不然 e^大数 会溢出)——这是生产里真会踩的坑。
# ══════════════════════════════════════════════════════════
def softmax(scores: np.ndarray) -> np.ndarray:
    # axis=1 = "沿着每一行操作";keepdims=True = 结果保持二维 (n,1),好跟 (n,n) 做广播减法
    shifted = scores - np.max(scores, axis=1, keepdims=True)   # 每行减本行最大值 → 防 e^大数 溢出
    exp = np.exp(shifted)                                       # 逐元素取 e^x(负数→0~1,0→1)
    return exp / np.sum(exp, axis=1, keepdims=True)             # 每行除以本行之和 → 每行加起来=1


# ══════════════════════════════════════════════════════════
# 该你写②:attention 本体 —— 三步,就是 attention 的全部灵魂
#   1) scores = Q · Kᵀ         每个词 × 每个词 的"相似度打分"(点积,越像分越高)
#   2) weights = softmax(scores)   每一行归一成权重(这行词该从各词各拿多少)
#   3) out = weights · V         用权重去【加权融合】所有词的信息
#   返回:(out, weights) —— out 是每个词的新表示,weights 是注意力矩阵(拿来解释"谁在看谁")
# ══════════════════════════════════════════════════════════
def attention(Q, K, V):
    scores = Q @ K.T            # (n,n):第 i 行第 j 列 = 词i·词j 的点积相似度(越像分越高)
    weights = softmax(scores)   # (n,n):每行归一成权重(词i 该从各词各拿多少)
    out = weights @ V           # (n,d):用权重加权融合所有词的 V,得到每个词的新表示
    return out, weights


if __name__ == "__main__":
    out, weights = attention(Q, K, V)

    print("🔎 注意力矩阵(第 i 行 = 词 i 把注意力分给了谁,一行加起来=1):")
    print("      " + "  ".join(f"{t:>4}" for t in tokens))
    for t, row in zip(tokens, weights):
        print(f"{t:>4}  " + "  ".join(f"{w:0.2f}" for w in row))

    print("\n💡 预期:'猫'那一行,应该给'猫'和'老鼠'较高权重(它俩向量像);")
    print("        '追'那一行,应该给'追'和'跑'较高权重。这就是模型'看懂谁跟谁相关'。")
    print("\n🆕 融合后每个词的新表示(已经掺入了相关词的信息,不再是孤立的 embedding):")
    print(out)
