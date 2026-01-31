import json
import aiohttp
import asyncio


async def query_express(express_num):
    """
    查询运单号（异步版本）
    :param express_num: 快递单号
    :return:
    """
    # 接口URL
    url = "http://api.officesee.com/kuaidi/kuaidi.ashx"

    # 请求参数
    params = {
        "user": "tb2026010908",
        "no": "%s:0000" % express_num
    }

    try:
        # 发送异步GET请求
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params, timeout=aiohttp.ClientTimeout(total=10)) as response:
                response.raise_for_status()
                text = await response.text()
                return text

    except aiohttp.ClientError as e:
        print(f"Network error: {e}")
        return """{
            "status": "201",
            "msg": "网络错误！",
            "result": {}
        }"""
    except asyncio.TimeoutError:
        print("Request timeout")
        return """{
            "status": "201",
            "msg": "请求超时！",
            "result": {}
        }"""
    except Exception as e:
        print(f"Other error: {e}")
        return """{
            "status": "202",
            "msg": "其他错误！",
            "result": {}
        }"""

# 调用方法
# async def test():
#     ret = json.loads(await query_express('9475422461578'))
#     print(ret)
#     print(type(ret))
# asyncio.run(test())
