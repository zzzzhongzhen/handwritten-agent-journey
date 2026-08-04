# 第 2 周 · 发 HTTP 请求(httpx)
# 先装:uv add httpx
# 运行:uv run 08_http_requests.py
# 需要联网。对照 Swift 的 URLSession。

import httpx
import json
# ============================================================
# 1. 最简单的 GET 请求
#    httpx.get(网址) → 拿回一个"响应对象" response
#    对照 Swift:URLSession.shared.data(from: url)
# ============================================================
# 这是个免费的测试 API(假数据,专门给人练手的),不需要 key
url = "https://jsonplaceholder.typicode.com/todos/1"

response = httpx.get(url)

# ============================================================
# 2. 响应对象里有什么
# ============================================================
print(f"① 状态码: {response.status_code}")   # 200 = 成功;404 = 找不到;500 = 服务器错
print(f"② 原始文本: {response.text}")          # 返回的原始字符串(是 JSON 格式的字符串)

print(f"response的类型是： {type(response)}")
# ============================================================
# 3. ⭐ response.json() —— 直接把返回的 JSON 解析成 Python dict
#    httpx 帮你做了 json.loads(),不用自己转!
# ============================================================
data = response.json()          # JSON 字符串 → dict
print(f"③ 解析后的 dict: {data}")
print(f"   它的类型: {type(data)}")            # <class 'dict'>
print(f"   取某个字段 title: {data['title']}")  # 像字典一样取值

# ============================================================
# 4. 判断请求成功没有(生产代码必做)
# ============================================================
if response.status_code == 200:
    print("④ 请求成功")
else:
    print(f"④ 请求失败,状态码 {response.status_code}")

# ============================================================
# 5. 加上异常处理(网络会超时、断网、DNS 失败……用你上节学的 try/except)
# ============================================================
def fetch_todo(todo_id):
    url = f"https://jsonplaceholder.typicode.com/todos/{todo_id}"
    try:
        response = httpx.get(url, timeout=10)   # timeout=10 秒,超时就抛异常
        response.raise_for_status()             # 状态码不是 2xx 就抛异常
        return response.json()
    except httpx.TimeoutException:
        print("⑤ 请求超时了")
        return None
    except httpx.HTTPStatusError as e:
        print(f"⑤ 服务器返回错误: {e}")
        return None
    except httpx.RequestError as e:            # 断网、DNS 失败等
        print(f"⑤ 网络出问题: {e}")
        return None

result = fetch_todo(2)
print(f"⑥ 安全获取的结果: {result}")

# ============================================================
# 6. 传查询参数(params)—— 相当于网址后面 ?key=value
# ============================================================
# 下面这个 API 会把你发的参数原样返回,方便你看效果
r = httpx.get("https://httpbin.org/get", params={"name": "byron", "job": "agent"})
print(f"⑦ 带参数请求,服务器收到的 args: {r.json()['args']}")

# ============================================================
# 🎯 你来练(2 个 TODO)
# ============================================================

# TODO 1:请求 https://jsonplaceholder.typicode.com/users/1
#         解析成 dict,打印出这个用户的 name 和 email。
# 提示:r = httpx.get(url);data = r.json();data["name"] / data["email"]

def myhttprequest1():
    test1_url = "https://jsonplaceholder.typicode.com/users/1"
    try:
        test1_response = httpx.get(test1_url)
        test1_response.raise_for_status()
        return test1_response
    except httpx.TimeoutException:
        print(f"{test1_url}接口请求超时了")
        return None
    except httpx.HTTPStatusError as e:
        test1_code = test1_response.status_code
        print(f"请求失败了,错误码为: {test1_code}, 错误为：{e}")
        return None
    except httpx.RequestError as e:
        print(f"请求request失败{e}")
        return None
response = myhttprequest1().text
response_dict = json.loads(response)
print(f"name={response_dict['name']} email={response_dict['email']}")

# TODO 2:用上面写好的 fetch_todo 函数,获取 todo_id=3 的数据,
#         如果拿到了(不是 None),打印它的 title;如果是 None,打印"获取失败"。
# 提示:result = fetch_todo(3);用 if result: ... else: ...

result = fetch_todo(todo_id=3)
if result is None:
    print("获取失败")
else:
    print(result) 
