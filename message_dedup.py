"""
消息去重工具
用于防止重复处理相同的消息
"""
import time
from collections import OrderedDict
import hashlib
import json
import threading


class MessageDeduplicator:
    """消息去重器"""

    def __init__(self, max_size=1000, expire_seconds=60):
        """
        初始化去重器
        :param max_size: 最大缓存消息数量
        :param expire_seconds: 消息过期时间（秒），默认60秒
        """
        self.max_size = max_size
        self.expire_seconds = expire_seconds
        # 使用 OrderedDict 存储消息指纹和时间戳
        self.message_cache = OrderedDict()
        # 添加线程锁，防止并发竞态条件
        self._lock = threading.Lock()

    def _get_message_fingerprint(self, message_data):
        """
        生成消息指纹
        :param message_data: 消息数据字典
        :return: 消息指纹（MD5）
        """
        try:
            # 提取关键字段生成唯一标识
            # 注意：不使用 CreateTime 和 NewMsgId，因为服务器重发时这些字段可能不同
            # 只使用消息内容本身来判断是否重复
            key_fields = {
                'from': message_data.get('Data', {}).get('FromUserName', {}).get('string', ''),
                'content': message_data.get('Data', {}).get('Content', {}).get('string', ''),
                'type': message_data.get('Data', {}).get('MsgType', 0)
            }

            # 生成 JSON 字符串并计算 MD5
            fingerprint_str = json.dumps(key_fields, sort_keys=True, ensure_ascii=False)
            fingerprint = hashlib.md5(fingerprint_str.encode('utf-8')).hexdigest()

            return fingerprint

        except Exception as e:
            print(f"[去重] 生成消息指纹失败: {e}")
            # 如果失败，返回 None（不去重）
            return None

    def is_duplicate(self, message_data):
        """
        检查消息是否重复（线程安全）
        :param message_data: 消息数据字典
        :return: True 表示重复，False 表示新消息
        """
        fingerprint = self._get_message_fingerprint(message_data)

        if fingerprint is None:
            # 无法生成指纹，不去重
            return False

        current_time = time.time()

        # 使用线程锁保护整个检查-添加过程，防止并发竞态条件
        with self._lock:
            # 清理过期消息
            self._cleanup_expired(current_time)

            # 检查是否已存在
            if fingerprint in self.message_cache:
                print(f"[去重] 检测到重复消息，指纹: {fingerprint[:8]}...")
                return True

            # 添加到缓存
            self.message_cache[fingerprint] = current_time

            # 限制缓存大小
            if len(self.message_cache) > self.max_size:
                # 移除最老的消息
                self.message_cache.popitem(last=False)

            return False

    def _cleanup_expired(self, current_time):
        """清理过期的消息记录"""
        expired_keys = []

        for fingerprint, timestamp in self.message_cache.items():
            if current_time - timestamp > self.expire_seconds:
                expired_keys.append(fingerprint)
            else:
                # OrderedDict 是按插入顺序的，后面的更新
                break

        for key in expired_keys:
            del self.message_cache[key]

        if expired_keys:
            print(f"[去重] 清理了 {len(expired_keys)} 条过期消息记录")

    def get_stats(self):
        """获取去重器统计信息（线程安全）"""
        with self._lock:
            return {
                'cached_messages': len(self.message_cache),
                'max_size': self.max_size,
                'expire_seconds': self.expire_seconds
            }


# 创建全局去重器实例
# 修改为60秒过期，因为不使用时间戳，相同内容在短时间内应该被认为是重复
message_deduplicator = MessageDeduplicator(max_size=1000, expire_seconds=60)
