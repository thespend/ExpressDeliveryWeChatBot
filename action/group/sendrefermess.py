import json
import aiohttp
from env_loader import TOKEN


async def send_refer_message(group_wx_id, at_wx_id, content):
    """
    群里发送消息（异步版本）
    :param group_wx_id: 群微信ID！
    :param at_wx_id: 群里@谁微信ID！
    :param content: 发送消息内容！
    """
    url = "http://124.221.45.58/sendTextMessage"
    payload = {
        "toWxid": group_wx_id,
        "ats": at_wx_id,
        "content": content
    }
    headers = {
        'AUTHORIZATION': TOKEN,
        'Content-Type': 'application/json'
    }

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload, headers=headers, timeout=aiohttp.ClientTimeout(total=10)) as response:
                data = await response.read()
                return json.loads(data.decode("utf-8"))
    except Exception as e:
        print(f"Error sending message: {e}")
        return {"status": "error", "message": str(e)}
