import json
import asyncio
from env_loader import ROBOT_ID, RESPONSE_M, STO, ZTO, YDA, EMS, YTO, JTE, SFE, KEYWORDS
from action.group.sendrefermess import send_refer_message
from check import extract_express
import ast
from action.group.input_excel_address import record_to_excel_address
from action.group.input_excel import record_to_excel
from expressapi.Express_inquiry import query_express
from addgroupdata import append_group_data_to_json
from action.group.getgroupinfo import get_group_info

# 创建异步锁保护 group_dict 的更新操作
_group_dict_lock = asyncio.Lock()


async def schedule(group_dict, message):
    """
    接口调度（异步版本）
    :param group_dict:群数据！
    :param message: 消息！
    :return:
    """
    # 添加调试日志
    import logging
    logging.info(f"[调试] schedule() 函数被调用")

    # 接收等待处置的消息！
    message_data = json.loads(message)
    # 判断消息非自己发送！被动进行回复！
    if message_data['Data']['FromUserName']['string'] != ROBOT_ID:

        # 私聊>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>逻辑
        if '@chatroom' not in message_data["Data"]["FromUserName"]["string"]:
            return

        # 群聊>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>逻辑
        if '@chatroom' in message_data["Data"]["FromUserName"]["string"]:

            # 群聊文本事件
            if message_data["Data"]["MsgType"] == 1:
                # 将微信群名称和微信群ID写入groupdata/groupdata.json文件中。
                group_id = message_data["Data"]["FromUserName"]["string"]
                if group_id not in group_dict.values():
                    # 使用异步锁保护 group_dict 的更新操作
                    async with _group_dict_lock:
                        # 双重检查，避免重复写入
                        if group_id not in group_dict.values():
                            nickname = get_group_info(group_id).get('data', {}).get('nickName', '')
                            # await 异步函数调用，并获取更新后的数据
                            updated_dict = await append_group_data_to_json({
                                nickname: group_id
                            })
                            # 更新内存中的 group_dict
                            group_dict.clear()
                            group_dict.update(updated_dict)
                            print(f"[INFO] 新增群组: {nickname} -> {group_id}")

                # 获取消息中的微信ID和消息内容！
                who_wx_id = message_data["Data"]["Content"]["string"].split(":")[0]
                who_nick_name = message_data["Data"]["PushContent"].split(":")[0]
                message_text = message_data['Data']['Content']['string'].split(":")[-1]

                # 检查是否包含关键词
                has_keyword = any(keyword in message_text for keyword in ast.literal_eval(KEYWORDS))

                if has_keyword:
                    print("检测到关键词，开始处理消息...")

                    # 先对提问者进行回复！
                    await send_refer_message(
                        message_data["Data"]["FromUserName"]["string"],
                        who_wx_id,
                        "@%s%s" % (who_nick_name, RESPONSE_M)
                    )

                    # 处理快递任务
                    if '拦截' in message_text or '退回' in message_text or '拒收' in message_text:
                        print("处理拦截任务")
                        await process_express_task(group_dict, message_data, '拦截', message_text)
                    if '催件' in message_text or '催更' in message_text or '催促' in message_text:
                        print("处理催件任务")
                        await process_express_task(group_dict, message_data, '催件', message_text)
                    if '地址' in message_text:
                        print("处理改地址任务")
                        await process_express_task(group_dict, message_data, '改地址', message_text)

            # 群聊图片事件
            if message_data["Data"]["MsgType"] == 3:
                return

            # 群聊语音事件
            if message_data["Data"]["MsgType"] == 34:
                return

            # 群聊视频事件
            if message_data["Data"]["MsgType"] == 43:
                return


async def process_express_task(group_dict, message_data, task_type, msg_text):
    """处理快递任务的通用函数（异步版本）"""
    list_res = extract_express(msg_text)

    items_to_process = []

    # 先找出所有可能是运单号的内容
    possible_items = [item for item in list_res if any(char.isdigit() for char in item)]

    # 根据任务类型决定最终要处理的列表
    if task_type == '改地址':
        # 改地址只取第一个有效的单号
        if possible_items:
            items_to_process = possible_items[:1]
    else:
        # 其他任务（拦截、催件等）处理所有识别出的单号
        items_to_process = possible_items

    print(f"需要处理的单号: {items_to_process}")

    # 如果没有识别出需要处理的单号，直接返回
    if not items_to_process:
        print("未提取到有效运单号进行处理。")
        return

    # 循环处理运单号！
    for item in items_to_process:
        # 跳过非单号的文本项
        if not any(char.isdigit() for char in item):
            continue
        print(f"处理单号: {item}")

        # 定义快递公司和对应配置
        express_companies = {
            '9': ('邮政', EMS), '77': ('申通', STO), '73': ('中通', ZTO), '75': ('中通', ZTO),
            '78': ('中通', ZTO), '76': ('中通', ZTO),
            '3': ('韵达', YDA), '4': ('韵达', YDA), 'YT': ('圆通', YTO), 'yt': ('圆通', YTO),
            'JT': ('极兔', JTE), 'jt': ('极兔', JTE),
            'SF': ('顺丰', SFE), 'sf': ('顺丰', SFE)
        }

        company_info = None
        for prefix, info in express_companies.items():
            if item.startswith(prefix):
                company_info = info
                break

        # 没有匹配到快递公司情况！
        if not company_info:
            print(f"未找到匹配的快递公司: {item}")
            continue

        # 匹配到快递公司情况！
        company_name, group_list = company_info
        print(f"匹配到快递公司: {company_name}")

        # 邮政需要特殊处理，查询物流信息以确定具体网点
        # 注意：group_list为列表，如："['大鹏D邮政(安福县)售后对接群','大鹏D邮政(吉安)售后对接群','大鹏D邮政(吉水县)售后对接群']"

        if company_name == '邮政':
            result = json.loads(await query_express(item))
            api_status = result.get('status')
            # 查询结果失败逻辑！
            if api_status != "0":
                mess = f'邮政运单号：{item}查无物流信息！请检查单号是否录错有误！'
                # 回复给原始发件人
                await send_refer_message(
                    message_data['Data']['FromUserName']['string'],
                    message_data['Data']['Content']['string'].split(':')[0],
                    "@%s%s" % (message_data['Data']['PushContent'].split(':')[0], mess)
                )
                # 添加1秒延迟，防止发送过快
                await asyncio.sleep(1)
                # 跳过这个单号的后续处理
                continue

            # 查询结果成功逻辑！
            else:
                logistics_info = str(result.get('result', {}).get('list', []))

                target_branch = None
                if "吉安市行业客户大宗揽投部" in logistics_info:
                    target_branch = ('吉安邮政', '吉安')
                elif '安福县城东揽收部' in logistics_info:
                    target_branch = ('安福邮政', '安福县')
                elif '吉水县金滩揽收部' in logistics_info:
                    target_branch = ('吉水邮政', '吉水县')

                if not target_branch:
                    print(f"未匹配到具体网点: {logistics_info}")
                    continue

                branch_name, keyword = target_branch

                # 数据保存
                if task_type == '改地址':
                    print(f'{company_name}快递')
                    await record_to_excel_address(group_dict, message_data, branch_name, item, msg_text, task_type)
                else:
                    print(f'{company_name}快递')
                    await record_to_excel(group_dict, message_data, branch_name, item, task_type)
                print(f'{branch_name}{task_type}数据保存成功！')

                # 消息转发
                group_names = ast.literal_eval(group_list)
                target_group_name = next((g for g in group_names if keyword in g), None)

                if target_group_name:
                    group_id = group_dict.get(target_group_name)
                    if group_id:
                        forward_message = msg_text if task_type == '改地址' else f'{item} {task_type}'
                        print(f"准备向群组 {target_group_name} (ID: {group_id}) 发送消息: {forward_message}")
                        await send_refer_message(
                            group_id,
                            message_data['Data']['Content']['string'].split(':')[0],
                            forward_message
                        )

                    else:
                        print(f"未找到群组ID: {target_group_name}")
                else:
                    print(f"未找到包含关键词 '{keyword}' 的群组")

        else:
            # 其他快递直接转发
            print(f"处理{company_name}快递...")
            group_names = ast.literal_eval(group_list)
            for group_name in group_names:
                group_id = group_dict.get(group_name)

                if not group_id:
                    print(f"未找到群组: {group_name}")
                    continue

                # 数据保存
                if task_type == '改地址':
                    print(f'{company_name}快递:')
                    await record_to_excel_address(group_dict, message_data, f'{company_name}快递', item, msg_text, task_type)
                else:
                    print(f'{company_name}快递:')
                    await record_to_excel(group_dict, message_data, f'{company_name}快递', item, task_type)

                print(f'{company_name}{task_type}数据保存成功！')

                # 消息转发
                forward_message = msg_text if task_type == '改地址' else f'{item} {task_type}'
                print(f"准备向群组 {group_name} (ID: {group_id}) 发送消息: {forward_message}")
                await send_refer_message(
                    group_id,
                    message_data['Data']['Content']['string'].split(':')[0],
                    forward_message
                )

                # 添加1秒延迟，防止发送过快
                await asyncio.sleep(1)
