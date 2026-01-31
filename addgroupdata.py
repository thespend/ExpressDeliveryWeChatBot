import json
from filelock import FileLock
import asyncio


async def append_group_data_to_json(new_data):
    """
    向JSON文件追加数据，如果键已存在则跳过（异步线程安全版本）

    Args:
        new_data: 要追加的数据，字典格式

    Returns:
        更新后的完整数据字典
    """
    def _blocking_io():
        lock_file = 'groupdata/groupdata.json.lock'

        # 使用文件锁确保并发安全
        with FileLock(lock_file, timeout=10):
            # 读取现有数据
            try:
                with open('groupdata/groupdata.json', 'r', encoding='utf-8') as f:
                    existing_data = json.load(f)
            except FileNotFoundError:
                existing_data = {}

            # 只添加不存在的键
            updated = False
            for key, value in new_data.items():
                if key not in existing_data:
                    existing_data[key] = value
                    updated = True

            # 只有在有更新时才写回文件
            if updated:
                with open('groupdata/groupdata.json', 'w', encoding='utf-8') as f:
                    json.dump(existing_data, f, ensure_ascii=False, indent=4)

            return existing_data

    # 使用 asyncio.to_thread 在后台线程中执行同步的IO代码
    result = await asyncio.to_thread(_blocking_io)
    return result
