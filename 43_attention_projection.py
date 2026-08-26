# 🧠 Attention 升级:加上可学习投影 W_q / W_k / W_v
# 运行:.venv/bin/python 43_attention_projection.py
#
# 41 号我们偷懒令 Q=K=V=X(直接用词向量)。真模型不是这样:
#   Q = X·W_q   K = X·W_k   V = X·W_v      三个矩阵是【训练学出来的】。
# 意义:模型自己学会"该从哪个角度看相关性"。
#
# 这个文件用指代例子做对比,让你亲眼看到:
#   没投影 → "它"只会看自己(学不到指代);  加上学好的 W_q → "它"终于去看名词了。

import numpy as np
np.set_printoptions(precision=3, suppress=True)

# ── 精心设计的 embedding:每一维都有含义,方便你看懂 ──
#            [名词?, 动词?, 代词?, 猫特征]
tokens = ["小猫", "追", "老鼠", "它"]
X = np.array([
    [1.0, 0.0, 0.0,  1.0],   # 小猫:名词 + 猫特征
    [0.0, 1.0, 0.0,  0.0],   # 追:  动词
    [1.0, 0.0, 0.0, -1.0],   # 老鼠:名词 + 反猫特征
    [0.0, 0.0, 1.0,  0.0],   # 它:  代词(注意:它跟谁都不"像",第4维也不带任何实体信息)
])
d_k = X.shape[1]


def softmax(scores):
    z = scores - np.max(scores, axis=1, keepdims=True)
    e = np.exp(z)
    return e / np.sum(e, axis=1, keepdims=True)


# 真·公式:多了 /√d_k 缩放(防止点积数值过大、softmax 过尖)
def attention(Q, K, V):
    scores = (Q @ K.T) / np.sqrt(d_k)
    weights = softmax(scores)
    return weights @ V, weights


def show(title, weights, out):
    print(f"\n{'='*52}\n{title}\n{'='*52}")
    print("注意力矩阵(第 i 行 = 词 i 把注意力分给了谁):")
    print("        " + "  ".join(f"{t:>4}" for t in tokens))
    for t, row in zip(tokens, weights):
        print(f"  {t:>4}  " + "  ".join(f"{w:0.2f}" for w in row))
    print(f"\n  '它' 融合后的新向量 = {out[3]}")


# ── 情形 A:没有投影(Q=K=V=X),就是 41 号那套 ──
outA, wA = attention(X, X, X)
show("情形A:没有投影(Q=K=V=X)—— '它' 会怎样?", wA, outA)
print("  👉 看'它'那一行:它跟名词/动词都不'像'(维度正交),只能几乎全押在【自己】身上。")
print("     结果:'它'的新向量 ≈ 它自己,啥上下文都没吸收到。指代?学不到。")


# ── 情形 B:加上"学好的"投影矩阵 ──
# W_q:把"代词"这一维,翻译成"我要找名词"(第3维=代词 → 映到 第0维=名词方向的 Query)
W_q = np.array([
    [0, 0, 0, 0],
    [0, 0, 0, 0],
    [1, 0, 0, 0],   # ← 关键:代词维(输入第2维)→ 名词维(输出第0维)。这就是"学会:代词该去找名词"
    [0, 0, 0, 0],
], dtype=float)
W_k = np.eye(d_k)   # Key 先用单位矩阵(名词的"名词维"本就=1,天然是好招牌)
W_v = np.eye(d_k)   # Value 也先用单位矩阵(交出原始信息)

Q, K, V = X @ W_q, X @ W_k, X @ W_v
outB, wB = attention(Q, K, V)
show("情形B:加上学好的 W_q(代词→找名词)—— '它' 会怎样?", wB, outB)
print("  👉 看'它'那一行:注意力全跑到【小猫 + 老鼠】(两个名词)上了,不再自恋。")
print("     '它'的新向量吸收了名词信息(第0维=名词分量被拉起来)——它开始'懂'自己该指代名词。")

print(f"""
🎯 一句话:同样的词向量、同样的三步 attention,
   只因为 W_q 学到了'代词该去看名词',注意力矩阵就彻底变了。
   → 这三个矩阵(W_q/W_k/W_v)里的数字,就是训练在调的东西;
     '模型学会看什么',物理上就是'这几个矩阵被调成了什么样'。
   (真模型还会叠多头 + 多层,让'它'进一步在小猫/老鼠之间分辨谁饿了。)
""")
