import logging

#logger：日志记录器，提供了应用程序可以直接使用的接口
#handler：处理器，将（logger创建的）日志记录发送到合适的目的地
#Formatter：格式化器，指定日志显示的格式
#Level:级别，定义日志的严重程度，常见级别有 DEBUG,INFO,WARNING,ERROR和CRITICAL

def my_logger(logger_name, log_name):

    #创建一个logger日志记录器(优先权重高处理器)
    logger = logging.getLogger(logger_name)
    logger.setLevel(logging.DEBUG)

    #创建一个handler日志处理器，用于写入日志
    fh = logging.FileHandler(f'log/mylog/{log_name}',encoding='utf8')
    fh.setLevel(logging.DEBUG)

    #格式化器
    formatter = logging.Formatter(
        datefmt='%Y-%m-%d %H:%M:%S',
        fmt="%(asctime)s %(levelname)s %(filename)s：%(lineno)d %(message)s",
    )
    fh.setFormatter(formatter)

    #给logger添加 handler
    logger.addHandler(fh)

    #返回日志记录器
    return logger

# 申明并调用！
# logger = go_fish_log('loo','loo.log')
# logger.debug('测试信息debug')
# logger.info('测试信息info')
# logger.warning('测试信息warning')
# logger.error('测试信息error')
# logger.critical('测试信息critical')