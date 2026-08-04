# 🎯 第 1 周里程碑:单词计数脚本
# 目标:统计每个单词出现几次,打印出现最多的前 10 个。
# 运行:uv run 05_word_count.py
#
# 框架搭好了,你只需要填 4 个 TODO。卡住就看提示,还卡就问 Claude。

# 一段测试文字(随便找的,重复词很多,方便看效果)
text = """
the cat sat on the mat the cat is happy the dog sat on the log
the dog is happy the cat and the dog are friends the sun is bright
the cat likes the sun the dog likes the mat the end
"""

# ============================================================
# 步骤 1:把整段文字切成一个个单词
# 提示:字符串有个方法 .split() ,不传参数时会按空格/换行切开,返回一个 list
# 例如 "a b c".split() → ['a', 'b', 'c']
# ============================================================
words = text.split()   # TODO: 把 text 切成单词列表(用 .split())


# ============================================================
# 步骤 2:数每个单词出现几次,存进一个字典
# 提示:先建一个空字典 counts = {}
#       然后 for 循环遍历 words,每遇到一个词,就让它的计数 +1。
#       经典写法:counts[word] = counts.get(word, 0) + 1
#       (.get(word, 0) 的意思:取 word 的当前计数,没有就当 0)
# ============================================================
counts = {}
for word in words:
    counts[word] = counts.get(word, 0) + 1
    


# ============================================================
# 步骤 3:按出现次数从多到少排序
# 提示:用内置函数 sorted()
#   counts.items() 会得到 [('the', 12), ('cat', 4), ...] 这样的列表
#   sorted(counts.items(), key=lambda pair: pair[1], reverse=True)
#     - key=lambda pair: pair[1]  表示"按每一对里的第 2 个元素(次数)排序"
#     - reverse=True 表示从大到小
# (lambda 是"临时小函数",现在先照着用,不用深究)
# ============================================================
ranked = counts.items()
ranked = sorted(ranked, key=lambda pair: pair[1], reverse=True)

# ============================================================
# 步骤 4:打印前 10 名
# 提示:列表切片 ranked[:10] 就是前 10 个。
#       用 for 循环遍历,打印 "单词: 次数"
# ============================================================
print("出现最多的 10 个单词:")
# TODO: 遍历 ranked 的前 10 个,打印每个单词和它的次数
for key, value in ranked[:10]:
    print(f"{key} 次数：{value}")