"""
测试消息去重功能
"""
from message_dedup import MessageDeduplicator

def test_deduplicator():
    """测试去重器"""
    print("=" * 60)
    print("测试消息去重功能")
    print("=" * 60)

    dedup = MessageDeduplicator(max_size=100, expire_seconds=300)

    # 模拟相同的消息
    message1 = {
        "Data": {
            "FromUserName": {"string": "12345@chatroom"},
            "Content": {"string": "wxid_test:776434921968981 催件"},
            "CreateTime": 1737012345,
            "MsgType": 1
        }
    }

    # 完全相同的消息（模拟重复接收）
    message2 = {
        "Data": {
            "FromUserName": {"string": "12345@chatroom"},
            "Content": {"string": "wxid_test:776434921968981 催件"},
            "CreateTime": 1737012345,
            "MsgType": 1
        }
    }

    # 不同的消息
    message3 = {
        "Data": {
            "FromUserName": {"string": "12345@chatroom"},
            "Content": {"string": "wxid_test:776434921968982 催件"},
            "CreateTime": 1737012346,
            "MsgType": 1
        }
    }

    print("\n第1次检查消息1:")
    result1 = dedup.is_duplicate(message1)
    print(f"  结果: {'重复' if result1 else '新消息'} [OK]")
    assert result1 == False, "第一次应该是新消息"

    print("\n第2次检查消息1（相同消息）:")
    result2 = dedup.is_duplicate(message1)
    print(f"  结果: {'重复' if result2 else '新消息'} [OK]")
    assert result2 == True, "第二次应该检测为重复"

    print("\n第3次检查消息2（完全相同）:")
    result3 = dedup.is_duplicate(message2)
    print(f"  结果: {'重复' if result3 else '新消息'} [OK]")
    assert result3 == True, "应该检测为重复"

    print("\n第4次检查消息3（不同消息）:")
    result4 = dedup.is_duplicate(message3)
    print(f"  结果: {'重复' if result4 else '新消息'} [OK]")
    assert result4 == False, "不同消息应该是新消息"

    print("\n统计信息:")
    stats = dedup.get_stats()
    print(f"  缓存消息数: {stats['cached_messages']}")
    print(f"  最大缓存: {stats['max_size']}")
    print(f"  过期时间: {stats['expire_seconds']}秒")

    print("\n" + "=" * 60)
    print("[OK] 所有测试通过！")
    print("=" * 60)

if __name__ == "__main__":
    test_deduplicator()
