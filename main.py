import asyncio
import websockets
import json
import logging
import time
from env_loader import ROBOT_ID, SERVER_IP, SERVER_PORT
from schedule import schedule
from cutoff_reminder import initialize_cutoff_reminder
from message_dedup import message_deduplicator


# --- 基本配置 ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# --- WebSocket 连接配置 ---
WEBSOCKET_URI = f"ws://{SERVER_IP}:{SERVER_PORT}/ws"

# 心跳配置，建议60秒发送一次心跳！
HEARTBEAT_INTERVAL = 60
group_dict = {}
reminder_scheduler = None  # 截单提醒调度器


async def initialize_group_data():
    global group_dict
    try:
        group_dict = json.load(open('groupdata/groupdata.json', 'r', encoding='utf8'))
    except Exception as e:
        print(e)


async def send_heartbeat(websocket):
    """
    定期发送心跳包
    """
    while True:
        try:
            heartbeat_msg = {
                "type": "heartbeat",
                "robotid": ROBOT_ID,
                "timestamp": time.time()
            }
            await websocket.send(json.dumps(heartbeat_msg))
            logging.debug("心跳包已发送")
            await asyncio.sleep(HEARTBEAT_INTERVAL)
        except Exception as e:
            logging.error(f"发送心跳失败: {e}")
            break


async def main_async():
    """
    主异步函数：初始化所有组件并运行
    """
    global reminder_scheduler

    # 1. 初始化群组数据
    await initialize_group_data()
    logging.info("群组数据加载完成")

    # 2. 启动截单提醒调度器
    reminder_scheduler = initialize_cutoff_reminder(group_dict)
    if reminder_scheduler:
        logging.info("截单提醒调度器启动成功")
    else:
        logging.warning("截单提醒调度器启动失败或未配置")

    # 3. 运行 WebSocket 消息接收
    await receive_messages()


async def receive_messages():
    """
    连接到 WebSocket 服务器并持续接收回调消息!
    """
    # 无限循环，确保在断开连接后能自动重连
    reconnect_delay = 5  # 初始重连延迟
    max_reconnect_delay = 60  # 最大重连延迟

    while True:
        try:
            # 尝试连接到 WebSocket 服务器
            async with websockets.connect(
                    WEBSOCKET_URI,
                    ping_interval=20,  # 20秒发送一次ping
                    ping_timeout=10,  # 10秒内没收到pong认为连接断开
                    close_timeout=10  # 关闭超时
            ) as websocket:
                logging.info(f"成功连接到 WebSocket 服务器: {WEBSOCKET_URI}")
                # 重置重连延迟
                reconnect_delay = 5

                # 连接后立即发送robotid进行注册
                register_msg = json.dumps({"robotid": ROBOT_ID})
                await websocket.send(register_msg)
                logging.info(f"已向服务器注册robotid: {ROBOT_ID}")

                # 启动心跳任务
                heartbeat_task = asyncio.create_task(send_heartbeat(websocket))

                # 持续监听来自服务器的消息
                async for message in websocket:
                    try:
                        # 尝试将消息解析为JSON格式
                        message_data = json.loads(message)

                        # 处理连接确认消息
                        if message_data.get('type') == 'connection_ack':
                            logging.info(f"连接确认: {message_data.get('message')}")
                            continue

                        # 处理心跳回复
                        if message_data.get('type') == 'heartbeat_reply':
                            logging.debug(f"收到心跳回复: {message_data.get('timestamp')}")
                            continue

                        # 打印普通消息
                        logging.info("--- 收到新的消息 ---")
                        pretty_message = json.dumps(message_data, indent=4, ensure_ascii=False)
                        # print(pretty_message)

                        # 添加调试信息
                        msg_id = message_data.get('Data', {}).get('NewMsgId', 'unknown')
                        msg_time = message_data.get('Data', {}).get('CreateTime', 0)
                        msg_content = message_data.get('Data', {}).get('Content', {}).get('string', '')
                        from_user = message_data.get('Data', {}).get('FromUserName', {}).get('string', '')
                        msg_type = message_data.get('Data', {}).get('MsgType', 0)

                        # 计算消息指纹（用于调试）
                        fingerprint = message_deduplicator._get_message_fingerprint(message_data)

                        logging.info(f"[调试] ========== 收到消息 ==========")
                        logging.info(f"[调试] 消息ID: {msg_id}")
                        logging.info(f"[调试] 时间戳: {msg_time}")
                        logging.info(f"[调试] 发送者: {from_user}")
                        logging.info(f"[调试] 消息类型: {msg_type}")
                        logging.info(f"[调试] 内容: {msg_content[:100] if msg_content else 'N/A'}")
                        logging.info(f"[调试] 消息指纹: {fingerprint[:16] if fingerprint else 'None'}...")
                        logging.info(f"[调试] 当前缓存中有 {len(message_deduplicator.message_cache)} 条消息")

                        # 消息去重检查
                        if message_deduplicator.is_duplicate(message_data):
                            logging.warning("⚠️ ⚠️ ⚠️  检测到重复消息，跳过处理 ⚠️ ⚠️ ⚠️")
                            continue

                        logging.info(f"[调试] ✓ 新消息，准备处理...")

                        #################################################################
                        # 在这里可以添加您自己的过滤和处理逻辑！
                        # 使用 asyncio.create_task 并发处理消息，避免阻塞
                        asyncio.create_task(schedule(group_dict, pretty_message))
                        #################################################################

                    except json.JSONDecodeError:
                        # 如果消息不是有效的JSON，则直接打印原始字符串
                        logging.warning("收到的消息不是有效的JSON格式，打印原始消息:")
                        print(message)

                    logging.info("--- 消息处理完毕 ---\n")

                # 连接断开，取消心跳任务
                heartbeat_task.cancel()
                try:
                    await heartbeat_task
                except asyncio.CancelledError:
                    pass

        except (websockets.exceptions.ConnectionClosedError,
                websockets.exceptions.ConnectionClosedOK) as e:
            logging.error(f"连接断开: {e}。将在{reconnect_delay}秒后尝试重新连接...")
            await asyncio.sleep(reconnect_delay)
            reconnect_delay = min(reconnect_delay * 1.5, max_reconnect_delay)

        except ConnectionRefusedError as e:
            logging.error(f"连接被拒绝: {e}。将在{reconnect_delay}秒后尝试重新连接...")
            await asyncio.sleep(reconnect_delay)
            reconnect_delay = min(reconnect_delay * 1.5, max_reconnect_delay)

        except Exception as e:
            logging.error(f"发生未知错误: {e}。将在{reconnect_delay}秒后尝试重新连接...")
            await asyncio.sleep(reconnect_delay)
            reconnect_delay = min(reconnect_delay * 1.5, max_reconnect_delay)


# --- 主程序入口 ---
if __name__ == "__main__":
    logging.info("启动 WebSocket 客户端...")
    try:
        # 运行主异步函数（所有初始化和运行逻辑都在其中）
        asyncio.run(main_async())
    except KeyboardInterrupt:
        logging.info("客户端已手动停止。")
        # 关闭截单提醒调度器
        if reminder_scheduler:
            reminder_scheduler.shutdown()
    except Exception as e:
        logging.error(f"程序异常退出: {e}")
        # 关闭截单提醒调度器
        if reminder_scheduler:
            reminder_scheduler.shutdown()
