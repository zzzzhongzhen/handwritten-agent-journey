# Python 类(class)—— 给 iOS 老兵的 OOP 翻译课
# 运行:uv run 18_classes.py
# 你不是学 OOP(你比谁都熟),是学"Python 怎么写 OOP"。

# ============================================================
# 1. 基本类:__init__ 就是 init,self 必须显式写
# ============================================================
class Dog:
    def __init__(self, name: str, age: int = 1):   # 构造器,支持默认参数
        self.name = name        # 属性:__init__ 里赋值即创建,不用提前声明
        self.age = age

    def bark(self) -> str:      # ⭐ 每个方法第一个参数都是 self(Swift 隐式,Python 显式)
        return f"{self.name}: 汪!"

    def birthday(self):
        self.age += 1           # 方法里访问/修改属性都要带 self.

d = Dog("旺财")                 # 创建实例:不用 new,类名直接调用
print(d.bark())
d.birthday()
print(f"{d.name} 现在 {d.age} 岁")

# ============================================================
# 2. @dataclass —— Python 里最接近 Swift struct 的东西
#    只是装数据时用它,自动生成 __init__、好看的打印
#    (但注意:Python 没有值类型!一切皆引用)
# ============================================================
from dataclasses import dataclass

@dataclass
class WeatherResult:
    city: str
    temp: float
    unit: str = "°C"

w = WeatherResult("深圳", 28.2)
print(w)                        # WeatherResult(city='深圳', temp=28.2, unit='°C') 自动美观
print(w.temp)

# ============================================================
# 3. 继承(和 Swift 差不多,语法更简)
# ============================================================
class Animal:
    def __init__(self, name):
        self.name = name
    def speak(self):
        return "..."

class Cat(Animal):              # 括号里写父类(Swift 是 : Animal)
    def speak(self):            # 重写不用 override 关键字
        return f"{self.name}: 喵"

    def __init__(self, name, indoor: bool):
        super().__init__(name)  # 调父类构造器,和 Swift 的 super.init 同理
        self.indoor = indoor

c = Cat("咪咪", indoor=True)
print(c.speak())

# ============================================================
# 4. "私有"只是约定:下划线开头 = 请当我是私有(不强制)
# ============================================================
class BankAccount:
    def __init__(self):
        self._balance = 0       # 约定:外面别直接碰(但语言不拦你,没有 private)

    def deposit(self, amount):
        if amount > 0:
            self._balance += 1 * amount

    @property                   # 类似 Swift 的计算属性(只读 getter)
    def balance(self):
        return self._balance

acc = BankAccount()
acc.deposit(100)
print(acc.balance)              # 注意:@property 让它像属性一样访问,不用加()

# ============================================================
# 🎯 你来练:把你的 Agent 重构成一个类!(真实价值所在)
#    这是类的意义:把 16 号文件里散落的 messages/tools/循环 收纳成一个对象
# ============================================================
class ChatAgent:
    def __init__(self, system_prompt: str):
        # TODO 1: 初始化 self.messages,内容是带 system_prompt 的列表
        #        (提示:[{"role": "system", "content": system_prompt}])
        self.messages = [{"role": "system", "content": system_prompt}]
        
    def add_user_message(self, text: str):
        # TODO 2: 往 self.messages 里 append 一条 user 消息
        self.messages.append({"role": "user", "content": text})

    def history_length(self) -> int:
        return len(self.messages)

# 写完取消注释测试:
agent = ChatAgent("你是一个友好的助手")
agent.add_user_message("你好")
print(f"agent的长度是{agent.history_length()}")     # 应该是 2(system + user)
