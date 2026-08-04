# 第 2 周 · 周二(2h):异常处理 try/except
# 运行:uv run 06_exceptions.py
# 学法:对照 Swift 的 do/catch/try,体会差异。每段都跑一下看输出。

# ============================================================
# 1. 最基本的 try/except(对照 Swift do/catch)
#    Swift:  do { try something() } catch { print(error) }
# ============================================================
try:
    x = int("abc")          # 这行会抛 ValueError(字母转不成数字)
    print("这行不会执行")     # 出错后,try 里剩下的代码直接跳过
except ValueError:
    print("① 转换失败,但程序没崩,继续往下走")

# ============================================================
# 2. 抓住异常对象看细节(as e)
# ============================================================
try:
    nums = [1, 2, 3]
    print(nums[10])         # IndexError
except IndexError as e:
    print(f"② 越界了: {e}")   # e 里有具体报错信息

# ============================================================
# 3. 抓不同类型的异常,分别处理
#    (你第 1 周踩过的 KeyError / IndexError / ValueError 全在这)
# ============================================================
def safe_divide(a, b):
    try:
        return a / b
    except Exception:      # 除以 0
        print("③ 不能除以 0")
        return None

print(safe_divide(10, 2))          # 5.0
print(safe_divide(10, 0))          # None(被兜住了)

# ============================================================
# 4. 一次抓多种 + 兜底的 Exception
#    Exception 是"所有异常的爹",能抓住绝大多数错误(兜底用)
# ============================================================
def get_value(d, key):
    try:
        return d[key]
    except KeyError:
        return "(没这个 key)"
    except Exception as e:         # 兜底:其他没预料到的错
        return f"(未知错误: {e})"

user = {"name": "byron"}
print(get_value(user, "name"))     # byron
print(get_value(user, "age"))      # (没这个 key)

# ============================================================
# 5. else 和 finally
#    else:  没出错才执行
#    finally: 不管出没出错,最后都执行(常用于收尾/关文件)
# ============================================================
try:
    result = 10 / 2
except ZeroDivisionError:
    print("出错了")
else:
    print(f"④ 没出错,结果 {result}")   # 会执行
finally:
    print("⑤ 不管怎样都会执行(收尾)")   # 一定执行

# ============================================================
# 6. 主动抛异常 raise(你第 1 周在 ask_ok 里见过)
#    对照 Swift 的 throw
# ============================================================
def set_age(age):
    if age < 0:
        raise ValueError(f"年龄不能是负数: {age}")   # 主动抛
    return age

try:
    set_age(-5)
except ValueError as e:
    print(f"⑥ 拦住了非法输入: {e}")

def set_oop(num):
    if num < 10:
        raise ValueError("不可以小于10")
try:
    set_oop(9)
except ValueError as e:
    print(f"数字小于10{e}")
# ============================================================
# 🎯 你来练(2 个 TODO,写完跑一下)
# ============================================================

# TODO 1:下面这个函数会因为把字符串当数字加而崩溃。
#         用 try/except 兜住 TypeError,出错时返回 None。
def add_numbers(a, b):
    return a + b            # add_numbers(1, "x") 会崩 → 用 try/except 保护它

# 提示:把 return a + b 放进 try,except TypeError 时 return None

def add_numbers(a, b):
    try:
        return a + b
    except TypeError as e:
        return None
# 测试(你的实现对了,下面两行应该一个出数字一个出 None,都不崩):
print(add_numbers(3, 5))
print(add_numbers(3, "x"))


# TODO 2:写一个 safe_get(lst, i) 函数,安全地取列表第 i 个元素,
#         越界时返回 None 而不是崩溃。
# 提示:try 里 return lst[i],except IndexError 时 return None

def safe_get(list, i):
    try:
        return list[i]
    except IndexError as e:
        return None
    
print(safe_get([1, 2], 10)) 