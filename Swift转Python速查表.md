# Swift → Python 速查表(给 iOS 老兵)

> 你已经会编程,只需要看差异。对照着看,15 分钟过一遍,边写边查。

## 最大的心智差异
| 方面 | Swift | Python |
|------|-------|--------|
| 代码块 | `{ }` 花括号 | **缩进**(4 空格,缩进错了就报错) |
| 类型 | 静态,编译期检查 | 动态,运行期才知道(可加类型注解但不强制) |
| 空值 | `nil` + Optional | `None` |
| 语句结尾 | 可省分号 | 不写分号 |
| 命名习惯 | camelCase | snake_case(下划线) |

---

## 变量 / 常量
```swift
// Swift
var x = 5
let name = "Tom"
```
```python
# Python(没有 let/var,没有真正的常量,约定大写表示常量)
x = 5
name = "Tom"
PI = 3.14   # 全大写 = 约定俗成的"别改我"
```

## 字符串
```swift
let s = "Hello \(name), age \(age)"   // Swift 插值
```
```python
s = f"Hello {name}, age {age}"        # Python f-string(超常用)
```

## 数组 / List
```swift
var arr = [1, 2, 3]
arr.append(4)
arr.count
arr[0]
```
```python
arr = [1, 2, 3]
arr.append(4)
len(arr)        # 注意是 len(arr) 不是 arr.count
arr[0]
arr[-1]         # 负索引取最后一个,Python 特色
arr[1:3]        # 切片,取索引1到2
```

## 字典 / Dictionary
```swift
var dict = ["a": 1, "b": 2]
dict["a"]
```
```python
dict = {"a": 1, "b": 2}
dict["a"]
dict.get("c", 0)   # 取不到给默认值,避免崩溃
```

## 可选值 / None
```swift
var name: String? = nil
if let n = name { print(n) }
```
```python
name = None
if name is not None:
    print(name)
# 或更 Python 的写法:
if name:
    print(name)
```

## 函数
```swift
func add(a: Int, b: Int = 0) -> Int {
    return a + b
}
```
```python
def add(a, b=0):          # 默认参数同理
    return a + b

# 带类型注解版(推荐,你会喜欢):
def add(a: int, b: int = 0) -> int:
    return a + b
```

## 条件 / 循环
```swift
for i in 0..<5 { }
if x > 0 { } else { }
```
```python
for i in range(5):    # 0,1,2,3,4
    pass
if x > 0:
    pass
else:
    pass

for item in arr:      # 直接遍历元素(像 Swift 的 for-in)
    print(item)
```

## 列表推导式(Python 特色,很常用,Swift 没直接对应)
```swift
let doubled = arr.map { $0 * 2 }              // Swift
let evens = arr.filter { $0 % 2 == 0 }
```
```python
doubled = [x * 2 for x in arr]                # Python 推导式
evens = [x for x in arr if x % 2 == 0]
```

## async / await(你 iOS 用过,概念一样)
```swift
func fetch() async -> Data { ... }
let data = await fetch()
```
```python
import asyncio

async def fetch():
    ...

data = await fetch()          # 只能在 async 函数里 await
asyncio.run(main())           # 顶层入口用 asyncio.run 启动
```

## 类 / Class
```swift
class Dog {
    var name: String
    init(name: String) { self.name = name }
    func bark() { print("woof") }
}
```
```python
class Dog:
    def __init__(self, name):   # init 是 __init__
        self.name = name        # self 必须显式写,像 Swift 的 self 但每个方法第一个参数都要

    def bark(self):             # 每个方法第一个参数都是 self
        print("woof")

d = Dog("旺财")                 # 创建对象不用 new
```

## 错误处理
```swift
do { try something() }
catch { print(error) }
```
```python
try:
    something()
except Exception as e:
    print(e)
```

## 导入
```swift
import Foundation
```
```python
import json                    # 导入整个模块
from anthropic import Anthropic  # 只导入某个东西
```

---

## 容易踩的坑(iOS 来的人)
1. **缩进就是语法**。少个空格、tab 混空格 → 直接报错。用编辑器统一设成 4 空格。
2. **没有类型保护**。变量能随便变类型,运行才报错 → 建议养成写类型注解的习惯。
3. **`len(x)` 不是 `x.count`**。
4. **`==` 比较值,`is` 比较是否同一对象**(判断 None 用 `is None`)。
5. **可变默认参数的坑**:别写 `def f(x=[])`,用 `def f(x=None)` 然后函数里判空。

---

## 学习方式建议
- 这份表过一遍(15 分钟),不用背,知道"哦 Python 这样写"即可。
- 然后直接动手写第 1 周的练习(单词计数),需要啥查啥。
- **写代码时卡住 = 最好的学习时机**,查文档或问 Claude。
