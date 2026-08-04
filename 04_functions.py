# 周二(2h):函数 + 参数 + 类型注解 + 一点 async
# 运行:uv run 04_functions.py
# 学法:对照注释,想一下"Swift 里我会怎么写",体会差异。

# ============================================================
# 1. 最基本的函数(对照 Swift 的 func)
# ============================================================
# Swift:  func add(a: Int, b: Int) -> Int { return a + b }
def add(a, b):
    return a + b

print(add(3, 5))          # 8

       # -2
# ============================================================
# 2. 带类型注解的函数(推荐写法,你做 Swift 会喜欢)
#    注解只是"给人和工具看的提示",Python 运行时不强制检查,
#    但 VS Code 会用它给你更准的联想和报错。
# ============================================================
def greet(name: str, times: int = 1) -> str:
    #                          ↑ 默认参数,和 Swift 一样
    return f"你好 {name}," * times

print(greet("byron"))          # 用默认 times=1
print(greet("byron", 3))       # times=3,重复三遍

# ============================================================
# 3. 关键字参数:调用时可以指名道姓传参(Python 很常用)
# ============================================================
def make_user(name: str, job: str, city: str) -> dict:
    return {"name": name, "job": job, "city": city}

# 不用记参数顺序,直接指名,可读性好
u = make_user(name="byron", city="上海", job="iOS转Agent")
print(u)


# ============================================================
# 4. 函数可以返回多个值(Python 特色,Swift 用元组也行)
# ============================================================
def min_max(nums: list):
    return min(nums), max(nums)

low, high = min_max([3, 1, 9, 4])   # 一次接住两个返回值
print(f"最小 {low},最大 {high}")


# ============================================================
# 5. 一点点 async(你 iOS 用过,概念一样,先混个眼熟)
#    async def 定义异步函数,await 等它完成。
# ============================================================
import asyncio

async def slow_hello() -> str:
    await asyncio.sleep(1)      # 假装在等网络/IO,1 秒
    return "(1 秒后)hello from async"

async def main():
    result = await slow_hello()  # await:等异步函数出结果
    print(result)

asyncio.run(main())    # 顶层用 asyncio.run 启动异步世界
