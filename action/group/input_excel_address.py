from openpyxl import Workbook, load_workbook
from datetime import datetime
import os
import asyncio
from filelock import FileLock


# 生成聊天记录！
async def record_to_excel_address(group_dict, message_data: dict, express_name, mess_content, new_address, sort_name):
    """
    记录各群聊天信息（异步版本，带文件锁保护）。
    通过在独立线程中运行同步的文件IO操作，避免阻塞事件循环。
    :param group_dict:
    :param message_data: 回调消息！
    :param express_name；快递名称！
    :param mess_content: 消息体
    :param new_address:新地址
    :param sort_name:分类名称！
    :return:
    """

    def _blocking_io():

        # 获取群名称！使用群ID而不是发送者ID
        group_id = message_data['Data']['FromUserName']['string']
        nickname = get_key_by_value(group_dict, group_id)

        # 调试信息
        print(f"[DEBUG] 消息来源群ID: {group_id}")
        print(f"[DEBUG] 查找到的群名称: {nickname}")
        print(f"[DEBUG] group_dict 内容: {group_dict}")

        # 如果找不到群名称，使用群ID作为文件夹名
        if nickname is None:
            print(f"[WARNING] 未在 group_dict 中找到群ID {group_id} 对应的群名称，使用群ID作为文件夹名")
            nickname = group_id

        # 创建数据字典
        input_data = {
            'groupName': nickname,
            'whoSend': message_data['Data']['Content']['string'].split(':')[0],
            'ExpressName': express_name,
            'messageContent': mess_content,
            'newAddress': new_address,
            'dateTime': datetime.fromtimestamp(message_data['Data']['CreateTime'])
        }

        # 文件名根据微信ID动态生成
        filename = os.path.join(os.getcwd(), "record", nickname, f"{datetime.fromtimestamp(message_data['Data']['CreateTime']).strftime('%Y-%m-%d')}{sort_name}.xlsx")

        print(f"[DEBUG] 将要创建的文件路径: {filename}")

        # 创建目录（如果不存在）
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        print(f"[DEBUG] 目录已创建: {os.path.dirname(filename)}")

        # 使用文件锁确保并发安全
        lock_file = filename + ".lock"
        with FileLock(lock_file, timeout=10):
            # 检查文件是否存在
            if os.path.exists(filename):
                # 追加模式：加载现有工作簿
                wb = load_workbook(filename)
                ws = wb.active
            else:
                # 新建模式：创建新工作簿并添加表头
                wb = Workbook()
                ws = wb.active
                headers = ['groupName', 'whoSend', 'ExpressName', 'messageContent', 'newAddress', 'dateTime']
                ws.append(headers)

            # 准备数据行
            row_data = [
                input_data['groupName'],
                input_data['whoSend'],
                input_data['ExpressName'],
                input_data['messageContent'],
                input_data['newAddress'],
                input_data['dateTime']
            ]
            # 追加数据
            ws.append(row_data)
            # 保存工作簿
            wb.save(filename)
        return 'success'

    # 使用 asyncio.to_thread 在后台线程中执行同步的IO代码
    try:
        result = await asyncio.to_thread(_blocking_io)
        return result
    except Exception as e:
        print(f"Error during async excel address writing: {e}")
        return 'failed'


def get_key_by_value(dictionary, target_value):
    """根据value获取key"""
    for key, value in dictionary.items():
        if value == target_value:
            return key
    # 如果没找到，返回None
    return None
