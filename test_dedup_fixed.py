"""
测试修复后的去重功能（不使用时间戳）
"""
from message_dedup import MessageDeduplicator

def test_dedup_without_time():
    """测试去重器（不依赖时间戳）"""
    print("=" * 60)
    print("测试去重功能（模拟服务器重发）")
    print("=" * 60)

    dedup = MessageDeduplicator(max_size=100, expire_seconds=60)

    # 模拟第一次收到的消息
    message1 = {
        "Data": {
            "FromUserName": {"string": "12345@chatroom"},
            "Content": {"string": "wxid_test:776434921968981 催件"},
            "CreateTime": 1737012345,  # 时间戳1
            "NewMsgId": 100001,  # 消息ID1
            "MsgType": 1
        }
    }

    # 模拟服务器重发的相同消息（时间戳和ID不同）
    message2 = {
        "Data": {
            "FromUserName": {"string": "12345@chatroom"},
            "Content": {"string": "wxid_test:776434921968981 催件"},  # 内容相同
            "CreateTime": 1737012350,  # 时间戳2（不同）
            "NewMsgId": 100002,  # 消息ID2（不同）
            "MsgType": 1
        }
    }

    # 完全不同的消息
    message3 = {
        "Data": {
            "FromUserName": {"string": "12345@chatroom"},
            "Content": {"string": "wxid_test:776434921968982 拦截"},  # 内容不同
            "CreateTime": 1737012360,
            "NewMsgId": 100003,
            "MsgType": 1
        }
    }

    print("\n场景1: 第1次收到消息（776434921968981 催件）")
    print(f"  - CreateTime: {message1['Data']['CreateTime']}")
    print(f"  - NewMsgId: {message1['Data']['NewMsgId']}")
    result1 = dedup.is_duplicate(message1)
    print(f"  结果: {'[重复]' if result1 else '[新消息]'}")
    assert result1 == False, "第一次应该是新消息"
    print("  [OK] 通过")

    print("\n场景2: 服务器重发相同消息（时间戳和ID都不同）")
    print(f"  - CreateTime: {message2['Data']['CreateTime']} (与第1次不同)")
    print(f"  - NewMsgId: {message2['Data']['NewMsgId']} (与第1次不同)")
    print(f"  - 但内容完全相同")
    result2 = dedup.is_duplicate(message2)
    print(f"  结果: {'[重复]' if result2 else '[新消息]'}")
    assert result2 == True, "应该检测为重复（因为内容相同）"
    print("  [OK] 通过 - 成功识别重复！")

    print("\n场景3: 不同的消息（776434921968982 拦截）")
    result3 = dedup.is_duplicate(message3)
    print(f"  结果: {'[重复]' if result3 else '[新消息]'}")
    assert result3 == False, "不同内容应该是新消息"
    print("  [OK] 通过")

    print("\n" + "=" * 60)
    print("[SUCCESS] 所有测试通过！")
    print("=" * 60)
    print("\n关键改进：")
    print("- 去重不再依赖 CreateTime 和 NewMsgId")
    print("- 只要消息内容（FromUserName + Content + MsgType）相同就会被识别为重复")
    print("- 即使服务器重发时使用不同的时间戳和ID，也能正确去重")

if __name__ == "__main__":
    test_dedup_without_time()
