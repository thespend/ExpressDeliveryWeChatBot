# env_loader.py
from dotenv import load_dotenv
import os

# 加载 .env 文件
load_dotenv()

# 环境变量
TOKEN = os.getenv('TOKEN')
ROBOT_ID = os.getenv('ROBOT_ID')
SERVER_IP = os.getenv('SERVER_IP')
SERVER_PORT = os.getenv('SERVER_PORT')
RESPONSE_M = os.getenv('RESPONSE_M')
KEYWORDS = os.getenv('KEYWORDS')
STO = os.getenv('STO')
ZTO = os.getenv('ZTO')
YDA = os.getenv('YDA')
EMS = os.getenv('EMS')
YTO = os.getenv('YTO')
JTE = os.getenv('JTE')
SFE = os.getenv('SFE')

# 截单提醒配置
CUTOFF_REMINDER_MESSAGE = os.getenv('CUTOFF_REMINDER_MESSAGE', '亲，今日的截单点（{time}）将至，麻烦检查一下系统里是否有未审核的订单，谢谢！')
ADVANCE_REMINDER_MINUTES = int(os.getenv('ADVANCE_REMINDER_MINUTES', '30'))
