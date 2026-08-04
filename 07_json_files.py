# 第 2 周 · 文件读写 + JSON
# 运行:uv run 07_json_files.py
# 学法:对照 Swift 的 FileManager / Codable / JSONEncoder。每段跑一下看效果。

import json

# ============================================================
# 1. 写文件(w = write,会覆盖原内容)
#    with ... as f:  用完自动关闭文件,不用手动 close()
#    (类似 Swift 的 defer / 自动资源管理)
# ============================================================
with open("note.txt", "w", encoding="utf-8") as f:
    f.write("我在学 Python\n")       # \n 换行
    f.write("今天学文件读写\n")
print("① 写完了,去目录里看看 note.txt")


# ============================================================
# 2. 读文件(r = read,默认就是 r)
# ============================================================
with open("note.txt", "r", encoding="utf-8") as f:
    content = f.read()               # 一次读全部,返回一个字符串
print(f"② 读到的内容:\n{content}")

# ---- 逐行读(大文件常用,一行行处理不撑爆内存)----
with open("note.txt", "r", encoding="utf-8") as f:
    for line in f:                   # 直接遍历 f = 逐行
        print(f"③ 一行: {line.strip()}")   # strip() 去掉行尾换行

# ---- 追加(a = append,不覆盖,接在后面写)----
with open("note.txt", "a", encoding="utf-8") as f:
    f.write("这行是追加的\n")

def open_note():
    with open("note.txt", "r", encoding="utf-8") as f:
        returnvalue = f.read()
    return returnvalue

print(f"这是我封装的函数进行读文件{open_note()}")
# ============================================================
# 3. JSON 核心:Python 对象 <-> JSON 字符串
#    这是和 API 对话的通用语言!
#
#    json.dumps(对象) → JSON 字符串   (dump-s: dump to string)
#    json.loads(字符串) → Python 对象  (load-s: load from string)
#
#    对照 Swift:dumps≈JSONEncoder,loads≈JSONDecoder
# ============================================================

# ---- Python dict → JSON 字符串 ----
me = {"name": "byron", "age": 33, "skills": ["iOS", "Python"], "active": True}
json_str = json.dumps(me, ensure_ascii=False)   # ensure_ascii=False 让中文正常显示
print(f"④ dict 转 JSON 字符串: {json_str}")
print(f"   它的类型是: {type(json_str)}")        # <class 'str'> —— 是字符串!

# ---- JSON 字符串 → Python dict ----
back = json.loads(json_str)
print(f"⑤ JSON 字符串转回 dict: {back}")
print(f"   现在能当字典用: {back['name']}")       # byron

py_list = [{"name": "byron", "age": 33, "skills": ["iOS", "Python"], "active": True}, {"name": "byron1", "age": 33, "skills": ["iOS"], "active": False}]
yy_json_str = json.dumps(py_list, ensure_ascii=False)
print(f"我自己制作的{yy_json_str} {type(yy_json_str)}")
py_back = json.loads(yy_json_str)
# ============================================================
# 4. 类型对照表(记住这个,API 返回的 JSON 你就会读了)
#    JSON        <->  Python
#    object {}    <->  dict
#    array []     <->  list
#    string       <->  str
#    number       <->  int / float
#    true/false   <->  True / False   (注意大小写!)
#    null         <->  None
# ============================================================

# ============================================================
# 5. 直接读写 JSON 文件(dump / load,没有 s,操作文件)
#    json.dump(对象, f)  → 写进文件
#    json.load(f)        → 从文件读出来
# ============================================================
data = {"task": "学 JSON", "done": False, "hours": 1.5}

with open("data.json", "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=2)   # indent=2 美化缩进,好读
print("⑥ 写好 data.json 了,打开看看格式")

with open("data.json", "r", encoding="utf-8") as f:
    loaded = json.load(f)
print(f"⑦ 从文件读回来: {loaded}")
print(f"   取某个值: {loaded['task']}")

# ============================================================
# 🎯 你来练(2 个 TODO)
# ============================================================

# TODO 1:有下面这个字典,把它转成 JSON 字符串并 print 出来。
#         要求中文正常显示(别变成 你 这种)。
user = {"用户名": "byron", "目标": "Agent 工程师", "已学天数": 7}
# 提示:json.dumps(user, ensure_ascii=False)
my_jsonstr = json.dumps(user, ensure_ascii=False, indent=2)
print(my_jsonstr)

# TODO 2:下面是一段从"API"拿到的 JSON 字符串(模拟接口返回)。
#         把它解析成 Python 对象,然后打印出 city 和 temp 两个值。
api_response = '{"city": "上海", "temp": 28, "weather": "晴"}'
# 提示:先 data = json.loads(api_response),再 data["city"] / data["temp"]
def paraseJson(ssss: str):
    indexn = json.loads(ssss)
    print(f"两个对象city为{indexn["city"]}, temp:{indexn.get("tempsss", None)}")

paraseJson(api_response)

with open("note.txt", "r", encoding="utf-8") as f:
    for linesss in f.readlines():
        print(f"我的我的读取文件{linesss}")
