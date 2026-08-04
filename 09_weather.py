# 🎯 第 2 周里程碑:天气查询脚本
# 综合运用本周全部内容:httpx 发请求 + JSON 解析 + try/except + 文件写入
# 运行:uv run 09_weather.py
# 需要联网。
#
# 用的是 Open-Meteo:完全免费、不需要 API key 的天气接口。
# 框架搭好了,你填 5 个 TODO。卡住看提示,还卡问 Claude(我只给提示不给答案)。

import httpx
import json

# 几个城市的经纬度(查天气要用坐标)
CITIES = {
    "上海": (31.23, 121.47),
    "北京": (39.90, 116.41),
    "深圳": (22.54, 114.06),
}

# 选一个城市
city = "上海"
lat, lon = CITIES[city]

# Open-Meteo 的接口地址 + 查询参数
url = "https://api.open-meteo.com/v1/forecast"
params = {
    "latitude": lat,
    "longitude": lon,
    "current_weather": True,     # 要当前天气
}

# ============================================================
# 步骤 1:发请求,拿到响应,解析成 dict
# 提示:httpx.get(url, params=params, timeout=10),然后 .json()
#       整段用 try/except 包住(网络会失败)
# ============================================================
try:
    # TODO 1: 发 GET 请求(带上 url 和 params),存到 response
    response = httpx.get(url, params=params, timeout=10)
    response.raise_for_status()          # 状态码不对就抛异常

    # TODO 2: 把 response 解析成 dict,存到 data
    data = response.json()

    # ⭐ 先把 data 整个打印出来看看结构!(不知道字段名就没法取值)
    print("原始返回:")
    print(json.dumps(data, ensure_ascii=False, indent=2))

    # ============================================================
    # 步骤 3:从 data 里取出当前天气
    # 提示:先看上面打印的结构,当前天气在 data["current_weather"] 里,
    #       里面有 temperature(温度)和 windspeed(风速)
    # ============================================================
    # TODO 3: 取出 current_weather 这个字典
    current = data['current_weather']

    # TODO 4: 从 current 里取温度和风速,打印成一句人话
    #         比如:上海 当前温度 28.5°C,风速 10.2 km/h
    print("=" * 30)
    # 在这里写打印语句
    print(f'{city} 当前温度{current['temperature']}C, 风速{current['windspeed']}km/h')
    # ============================================================
    # 步骤 4:把结果存进文件(json.dump)
    # 提示:open("weather.json", "w", encoding="utf-8") + json.dump(...)
    #       记得 ensure_ascii=False, indent=2
    # ============================================================
    # TODO 5: 把 data 写进 weather.json 文件
    with open('weather.json', 'w', encoding='utf-8') as f:
        # 转成json字符串
        json.dump(data, f, ensure_ascii=False, indent=2)
    print("已保存到 weather.json")

except httpx.RequestError as e:
    print(f"网络出问题了: {e}")
except httpx.HTTPStatusError as e:
    print(f"服务器返回错误: {e}")
except Exception as e:
    print(f"其他错误: {e}")

def your_test():
    url = "https://api.open-meteo.com/v1/forecast"
    try:
        response = httpx.get(url, timeout=10)
        response.raise_for_status()
    except httpx.TimeoutException as e:
        print(e)
        return None
    except httpx.HTTPStatusError as e:
        print(e)
        return None
    except httpx.RequestError as e:
        print(e)
        return None
    else:
        print("请求成功")
        return response.json()
    