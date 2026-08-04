# 你的第一段 Python 代码。跑通它,今天就算赢 🎉
# 运行方式(在终端):uv run test.py

# --- 1. 变量 + f-string 字符串插值(对应 Swift 的 \(name)) ---
name = "byron"
print(f"我开始学 Python 了,我是 {name}")

# --- 2. list 列表(对应 Swift 的 Array) ---
nums = [1, 2, 3, 4, 5]
print(f"原始列表: {nums}")
print(f"列表长度: {len(nums)}")     # 注意:len(nums) 不是 nums.count
print(f"第一个: {nums[0]},最后一个: {nums[-1]}")   # -1 取最后一个,Python 特色
print("测试越界访问:")

# --- 3. 列表推导式(Python 特色,Swift 的 map 差不多) ---
doubled = [x * 2 for x in nums]
print(f"每个翻倍: {doubled}")

evens = [x for x in nums if x % 2 == 0]   # 带过滤,相当于 filter
print(f"只留偶数: {evens}")

# --- 4. dict 字典(对应 Swift 的 Dictionary) ---
me = {"job": "iOS", "goal": "Agent 工程师"}
print(f"我现在是 {me['job']},目标是 {me['goal']}")

# --- 5. for 循环 + 条件 ---
for n in nums :
    if n > 3:
        print(f"{n} 比 3 大")
    else:
        print(f"{n} 不大于 3")

name = "1ss"
if name is None :   # Python 里判断是否为 None 用 is
  print(f"名字是 {len(name)}")

x = str(1)
if x == 1:
    print(f"{x} 是正数")
elif x == "2":
    print(f"{x} 是零")
else:
    print(f"{x} 是负数")

users = {"hans": "active", "byron": "inactive"}
for name, status in users.copy().items():
    if status == "inactive":
        print(f"{name} 是活跃用户")
        del users[name]

print(users)

xxxx = list(range(5, 10, 3))
print(f"这个列表是:{xxxx}")

result = sum(xxxx)
print(f"1到9的和是:{result}")

for n in range(2, 10):
    for x in range(2, n):
        if n % x == 0:
            print(f"{n} 可以被 {x} 整除")
            break
        print(f"{n} 不能被 {x} 整除")
    else:
        print(f"{n} 是质数")

class MyClass:
    pass

command = "1 2 3"
match command.split():
    case ["go", direction]:
        print(f"你要去 {direction}")
    case ["pick", "up", item]:
        print(f"你要捡起 {item}")
    case [1, 2, 3]:
        print("匹配到 [1, 2, 3]")

def ask_ok(prompt, retries = 4):
    while True:
        replay = input(prompt)
        if replay in {'y', 'ye', 'yes'}:
            return True
        if replay in {'n', 'no', 'nop', 'nope'}:
            return False
        retries = retries - 1
        if retries < 0:
            raise ValueError('invalid user response')

def fList(a, L=[]):
    L.append(a)
    return L
fList(1)
fList(2)
print(fList(3))

def parrot(voltage, state = 'a stiff', action = 'voom'):
    print(f"-- This parrot wouldn't {state} if you put {voltage} volts through it. E's {action}!")

parrot('bleep', action = 1000)

def cheeseshop(kind, address, *args, **kwargs):
    print(f"-- {kind} {address} cheese shop")
    for arg in args:
        print(arg)
    for kw in kwargs:
        print(f"{kw}: {kwargs[kw]}")
cheeseshop('beauty', 'option1', 'option2', keyword1='value1', keyword2='value2')

def createUser(name, *, is_admin):
    print(f"创建用户 {name},是否管理员: {is_admin}")
createUser("byron", is_admin=True)


def greet(name, greeting="你好"):
    print(f"{greeting} {name}")
info = {"name": "byron", "greeting": "Hello"}
greet(**info)

def make_incrementor(n):
    return lambda x: x + n
f = make_incrementor(42)
print(f(1))
print(f(2))
    
data = sorted([5, 2, 3, 1, 4], key=lambda x: -x)
print(data)


def pair(x):
    return (x[1])
pairs = [(1, 'one'), (2, 'two'), (3, 'three'), (4, 'four')]
pairs.sort(key=pair)
print(pairs)


def my_function():
    """Do nothing, but document it.

    No, really, it doesn't do anything.
    """
print(my_function.__doc__)

fruits = ['orange', 'apple', 'pear', 'banana', 'kiwi', 'apple', 'banana']
print(fruits.count('apple'))
print(fruits.index('apple', 2))
print(fruits.pop(1))


from collections import deque

squares = [n**2 for n in range(10)]
print(squares)

filter = [x for x in [0, 1, -9, -2] if x >= 0]
print(filter)

tupleArray = [(x, y) for x in [1, 2, 3] for y in [3, 1, 4] if x != y]
print(tupleArray)
del tupleArray[:]
print(f"del{tupleArray}")

t = 12, 34, "222"
print(t[0])

basket = {'apple', 'orange', 'apple', 'pear', 'orange', 'banana'}
print("orange" in basket)

a = set("abracadabra")
b = set("alacazam")
print(a - b)  # 在 a 中但不在 b 中的元素
print(a | b)  # 在 a 或 b 中的元素
print(a & b)  # 在 a 和 b 中的元素
print(a ^ b)  # 在 a 或 b 中但不在两者中的元素

a = {x for x in 'abracadabra' if x not in 'abc'}
print(a)

tel = {'one': 1, 'two': 2, 'three': 3}
del tel['one']
print(list(tel))

zidiantuidaoshi = {x: x**2 for x in (2, 4, 6)}
print(zidiantuidaoshi)

tds = dict(sape=1, guido="22", jack=3)
print(tds)

for key, value in tds.items():
    print(f"{key} = {value}")

questions = ['name', 'quest']
answers = ['lancelot', 'the holy grail', 'blue']
for q, a in zip(questions, answers):
    print(f"what is your{q}? it is {a}")

print(reversed(answers))

import math

if not math.isnan(value):
    print('nnnnssssnnnnnsss')

print("Apple" < "apple")

    