# 🎲 从「融合后向量」到「吐出下一个 token」—— 接着 41 号往下演
# 运行:.venv/bin/python 42_next_token.py
#
# 41 号我们让 attention 把每个词的信息融合好了。但那还不是"预测"。
# 这个文件补上最后一段:最后一层向量 → LM head → logits → softmax → 概率 → 采样 → 下一个词。
# 关键:attention 负责"理解上下文",LM head 负责"吐字"。是两回事。

import numpy as np
np.set_printoptions(precision=3, suppress=True)

# ── 假装 41 号已经跑完:输入"猫 追 老鼠",最后一层在【最后一个位置(老鼠)】的输出向量 ──
# 真模型这里是 d=3584 维;我们用 d=4 的小向量,规律一样。
last_hidden = np.array([0.847, 0.145, 0.815, 0.193])   # ← 就是 41 号 out 的"老鼠"那一行

# ── 词表:真模型 15 万词;我们缩成 6 个候选,看得清 ──
VOCAB = ["跑", "吃", "。", "睡觉", "老鼠", "追"]

# ── LM head:形状 [词表大小, d]。每一行 = 一个词的"标签向量"。
#    某个词的 logit = last_hidden 跟该词标签向量的点积(又是点积相似度!越像分越高)。
#    真模型里这个矩阵是训练学出来的;这里手捏,让"跑/吃"跟 last_hidden 更像。 ──
W_lm = np.array([
    [0.9, 0.1, 0.8, 0.2],   # 跑    ← 故意跟 last_hidden 很像 → logit 高
    [0.8, 0.2, 0.7, 0.1],   # 吃    ← 也挺像
    [0.1, 0.1, 0.1, 0.1],   # 。
    [0.3, 0.6, 0.2, 0.5],   # 睡觉
    [0.2, 0.0, 0.2, 0.9],   # 老鼠
    [0.0, 0.9, 0.1, 0.8],   # 追
])


def softmax(z):   # 你在 41 号写过的同一个函数(这里是一维版)
    z = z - np.max(z)
    e = np.exp(z)
    return e / np.sum(e)


if __name__ == "__main__":
    # ③ LM head:向量 → 每个词一个原始分(logit)
    logits = W_lm @ last_hidden
    print("① logits(每个词的原始分,没归一,可正可负):")
    for w, l in zip(VOCAB, logits):
        print(f"    {w:>4}  {l:+.3f}")

    # ④ 温度:logits / T 再 softmax。T 小→分布更尖(更确定);T 大→更平(更随机)
    for T in (0.5, 1.0, 2.0):
        probs = softmax(logits / T)
        top = VOCAB[int(np.argmax(probs))]
        print(f"\n② 温度 T={T}:概率分布(贪心会选 → 「{top}」)")
        for w, p in sorted(zip(VOCAB, probs), key=lambda x: -x[1]):
            bar = "█" * int(p * 40)
            print(f"    {w:>4}  {p:0.3f}  {bar}")

    print("\n💡 看懂三件事:")
    print("   • logit 高 = 这个词的'标签向量'跟当前语义向量像(又是点积,跟 attention 一个套路)")
    print("   • 温度 T 只除在 logits 上:T→0 逼近贪心(永远选最大),T 大概率被拉平(更敢乱选)")
    print("   • '吐字'靠的是 LM head+softmax+采样,attention 只管把上下文揉进向量里")
