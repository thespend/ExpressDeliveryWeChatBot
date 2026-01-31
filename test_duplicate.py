"""
测试重复处理问题
"""
import json
import asyncio
from schedule import schedule

# 模拟消息数据
test_message = {
    "Data": {
        "FromUserName": {"string": "12345@chatroom"},
        "Content": {"string": "wxid_test:776434921968981 催件"},
        "PushContent": "测试用户:776434921968981 催件",
        "MsgType": 1,
        "CreateTime": 1737012345
    }
}

# 模拟群组数据
test_group_dict = {
    "测试群": "12345@chatroom",
    "申通售后群": "50066595729@chatroom"
}

async def test_duplicate():
    """测试是否会重复处理"""
    print("=" * 60)
    print("开始测试重复处理问题")
    print("=" * 60)

    message_json = json.dumps(test_message, indent=4, ensure_ascii=False)

    print("\n测试消息:")
    print(message_json)

    print("\n开始处理消息...")
    print("=" * 60)

    # 调用一次 schedule 函数
    await schedule(test_group_dict, message_json)

    print("=" * 60)
    print("处理完成")
    print("=" * 60)
    print("\n请检查：")
    print("1. 是否向申通售后群发送了几次消息？")
    print("2. Excel 中保存了几条数据？")
    print("3. 控制台输出了几次'处理催件任务'？")

if __name__ == "__main__":
    asyncio.run(test_duplicate())
