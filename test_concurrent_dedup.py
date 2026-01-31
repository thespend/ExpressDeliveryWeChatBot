"""
测试消息去重器的并发安全性
模拟多个线程同时接收相同的消息
"""
import threading
import time
from message_dedup import MessageDeduplicator


def simulate_message_arrival(deduplicator, message, thread_id, results):
    """
    模拟消息到达并检查去重
    :param deduplicator: 去重器实例
    :param message: 消息数据
    :param thread_id: 线程ID
    :param results: 结果列表（用于记录哪些线程通过了去重检查）
    """
    # 模拟消息处理延迟（随机0-10毫秒）
    time.sleep(0.001 * (thread_id % 10))

    is_dup = deduplicator.is_duplicate(message)

    if not is_dup:
        # 如果不是重复消息，记录这个线程
        results.append(thread_id)
        print(f"[线程{thread_id}] [OK] 通过去重检查，准备处理消息")
    else:
        print(f"[线程{thread_id}] [SKIP] 检测为重复，跳过处理")


def test_concurrent_deduplication():
    """测试并发去重是否安全"""
    print("=" * 70)
    print("测试并发去重安全性")
    print("=" * 70)

    # 创建去重器
    dedup = MessageDeduplicator(max_size=100, expire_seconds=60)

    # 创建相同的消息
    message = {
        "Data": {
            "FromUserName": {"string": "12345@chatroom"},
            "Content": {"string": "wxid_test:776434921968981 催件"},
            "MsgType": 1
        }
    }

    # 用于记录哪些线程通过了去重检查
    results = []

    # 创建10个线程，模拟10个几乎同时到达的相同消息
    threads = []
    num_threads = 10

    print(f"\n创建 {num_threads} 个线程，模拟同时收到 {num_threads} 条相同消息...")
    print("预期结果：只有1个线程能通过去重检查\n")

    for i in range(num_threads):
        thread = threading.Thread(
            target=simulate_message_arrival,
            args=(dedup, message, i, results)
        )
        threads.append(thread)

    # 同时启动所有线程
    start_time = time.time()
    for thread in threads:
        thread.start()

    # 等待所有线程完成
    for thread in threads:
        thread.join()

    elapsed = time.time() - start_time

    # 检查结果
    print("\n" + "=" * 70)
    print(f"测试完成，耗时: {elapsed*1000:.2f}ms")
    print(f"通过去重检查的线程数: {len(results)}")
    print(f"通过去重检查的线程ID: {results}")
    print("=" * 70)

    if len(results) == 1:
        print("\n[SUCCESS] 测试通过！只有1个线程通过了去重检查")
        print(f"[SUCCESS] 并发安全修复成功！")
        return True
    else:
        print(f"\n[FAIL] 测试失败！有 {len(results)} 个线程通过了去重检查")
        print(f"[FAIL] 仍然存在并发问题！")
        return False


def test_different_messages():
    """测试不同消息不会被误判为重复"""
    print("\n\n" + "=" * 70)
    print("测试不同消息的去重")
    print("=" * 70)

    dedup = MessageDeduplicator(max_size=100, expire_seconds=60)

    messages = [
        {
            "Data": {
                "FromUserName": {"string": "12345@chatroom"},
                "Content": {"string": "wxid_test1:776434921968981 催件"},
                "MsgType": 1
            }
        },
        {
            "Data": {
                "FromUserName": {"string": "12345@chatroom"},
                "Content": {"string": "wxid_test2:776434921968982 拦截"},
                "MsgType": 1
            }
        },
        {
            "Data": {
                "FromUserName": {"string": "67890@chatroom"},
                "Content": {"string": "wxid_test3:776434921968983 催件"},
                "MsgType": 1
            }
        }
    ]

    results = []
    for i, msg in enumerate(messages):
        is_dup = dedup.is_duplicate(msg)
        if not is_dup:
            results.append(i)
            print(f"[消息{i+1}] [OK] 新消息")
        else:
            print(f"[消息{i+1}] [ERROR] 重复消息（异常！）")

    print("\n" + "=" * 70)
    if len(results) == len(messages):
        print(f"[SUCCESS] 测试通过！{len(messages)} 条不同消息都被正确识别为新消息")
        return True
    else:
        print(f"[FAIL] 测试失败！部分不同消息被误判为重复")
        return False


if __name__ == "__main__":
    print("\n开始测试消息去重器的并发安全性和准确性...\n")

    # 测试1：并发安全性
    test1_passed = test_concurrent_deduplication()

    # 测试2：不同消息不会被误判
    test2_passed = test_different_messages()

    # 总结
    print("\n\n" + "=" * 70)
    print("测试总结")
    print("=" * 70)
    print(f"并发安全性测试: {'[PASS]' if test1_passed else '[FAIL]'}")
    print(f"准确性测试: {'[PASS]' if test2_passed else '[FAIL]'}")

    if test1_passed and test2_passed:
        print("\n[SUCCESS] 所有测试通过！去重功能正常工作！")
    else:
        print("\n[FAIL] 部分测试失败，需要进一步检查")
    print("=" * 70)
