"""
截单提醒定时任务模块
功能：根据配置的截单时间点，提前发送截单提醒到指定客户群
"""
import json
import asyncio
import logging
from datetime import datetime, timedelta
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from env_loader import CUTOFF_REMINDER_MESSAGE, ADVANCE_REMINDER_MINUTES
from action.group.sendtaskmess import send_message


class CutoffReminderScheduler:
    """截单提醒调度器"""

    def __init__(self, group_dict):
        """
        初始化调度器
        :param group_dict: 群组数据字典 {群昵称: 群ID}
        """
        self.group_dict = group_dict
        self.scheduler = AsyncIOScheduler()
        self.task_config = {}

    def load_task_config(self):
        """加载截单任务配置"""
        try:
            with open('task/task.json', 'r', encoding='utf-8') as f:
                self.task_config = json.load(f)
            logging.info(f"截单任务配置加载成功: {len(self.task_config)}个时间点")
            return True
        except Exception as e:
            logging.error(f"加载截单任务配置失败: {e}")
            return False

    async def send_cutoff_reminder(self, cutoff_hour, group_names):
        """
        发送截单提醒
        :param cutoff_hour: 截单小时数（如15表示15:00）
        :param group_names: 需要提醒的客户群名称列表
        """
        cutoff_time = f"{cutoff_hour}:00"
        message_content = CUTOFF_REMINDER_MESSAGE.format(time=cutoff_time)

        logging.info(f"[截单提醒] 开始发送 {cutoff_time} 截单提醒，目标群数量: {len(group_names)}")

        for group_name in group_names:
            try:
                # 从group_dict中查找群ID
                group_id = self.group_dict.get(group_name)

                if not group_id:
                    logging.warning(f"[截单提醒] 未找到群组: {group_name}，请检查groupdata.json")
                    continue

                # 发送消息
                logging.info(f"[截单提醒] 准备向 [{group_name}] (ID:{group_id}) 发送提醒")
                result = await send_message(group_id, message_content)

                if result.get('status') == 'error':
                    logging.error(f"[截单提醒] 发送失败: {group_name} -> {result.get('message')}")
                else:
                    logging.info(f"[截单提醒] 发送成功: {group_name}")

                # 每条消息间隔1秒，避免发送过快
                await asyncio.sleep(1)

            except Exception as e:
                logging.error(f"[截单提醒] 发送异常: {group_name} -> {e}")

        logging.info(f"[截单提醒] {cutoff_time} 提醒发送完成")

    def start(self):
        """启动截单提醒调度器"""
        if not self.load_task_config():
            logging.error("截单提醒调度器启动失败：配置文件加载失败")
            return False

        if not self.task_config:
            logging.warning("截单提醒调度器：未配置任何截单时间点")
            return False

        # 为每个截单时间点创建定时任务
        for cutoff_hour, group_names in self.task_config.items():
            if not group_names:
                logging.warning(f"截单时间点 {cutoff_hour}:00 未配置客户群，跳过")
                continue

            # 计算提醒时间（截单时间 - 提前分钟数）
            cutoff_hour_int = int(cutoff_hour)
            reminder_time = datetime.now().replace(
                hour=cutoff_hour_int,
                minute=0,
                second=0,
                microsecond=0
            ) - timedelta(minutes=ADVANCE_REMINDER_MINUTES)

            reminder_hour = reminder_time.hour
            reminder_minute = reminder_time.minute

            # 创建cron触发器：每天在指定时间执行
            trigger = CronTrigger(
                hour=reminder_hour,
                minute=reminder_minute,
                second=0
            )

            # 添加定时任务
            self.scheduler.add_job(
                func=self.send_cutoff_reminder,
                trigger=trigger,
                args=[cutoff_hour, group_names],
                id=f'cutoff_reminder_{cutoff_hour}',
                name=f'截单提醒-{cutoff_hour}:00',
                replace_existing=True
            )

            logging.info(
                f"[截单提醒] 已配置定时任务: "
                f"{cutoff_hour}:00截单 -> 提前{ADVANCE_REMINDER_MINUTES}分钟 -> "
                f"每天{reminder_hour:02d}:{reminder_minute:02d}发送 -> "
                f"{len(group_names)}个客户群"
            )

        # 启动调度器
        try:
            self.scheduler.start()
            logging.info(f"[截单提醒] 调度器已启动，共配置 {len(self.task_config)} 个时间点")
            return True
        except Exception as e:
            logging.error(f"[截单提醒] 调度器启动失败: {e}")
            return False

    def shutdown(self):
        """关闭调度器"""
        if self.scheduler.running:
            self.scheduler.shutdown()
            logging.info("[截单提醒] 调度器已关闭")

    def get_jobs(self):
        """获取所有定时任务"""
        return self.scheduler.get_jobs()

    def print_jobs(self):
        """打印所有定时任务信息"""
        jobs = self.get_jobs()
        if not jobs:
            logging.info("[截单提醒] 当前没有运行中的任务")
            return

        logging.info(f"[截单提醒] 当前运行中的任务 ({len(jobs)}个):")
        for job in jobs:
            logging.info(f"  - {job.name} | 下次执行: {job.next_run_time}")


# 创建全局调度器实例（将在main.py中初始化）
cutoff_reminder_scheduler = None


def initialize_cutoff_reminder(group_dict):
    """
    初始化并启动截单提醒调度器
    :param group_dict: 群组数据字典
    :return: 调度器实例
    """
    global cutoff_reminder_scheduler

    cutoff_reminder_scheduler = CutoffReminderScheduler(group_dict)
    success = cutoff_reminder_scheduler.start()

    if success:
        cutoff_reminder_scheduler.print_jobs()

    return cutoff_reminder_scheduler if success else None
