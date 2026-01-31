import re
import ast
from env_loader import KEYWORDS


def check_conditions(text):
    """
    检查当前消息是否需要进行转发
    :param text: 待检查的文本
    :return: bool (True 表示需要转发)
    """
    # 1. 检查是否包含快递单号（77、73、75、78、9、3、4 开头的数字串）或 YT/JT/SF
    has_tracking_or_code = bool(
        # 任意位置匹配数字77|73|75|78|9|3|4开头的单号
        re.search(r'(77|73|75|78|9|3|4)\d+', text) or
        # 任意位置匹配YT|JT|SF字母
        re.search(r'(YT|JT|SF)', text)
    )

    # 2. 检查是否包含任意一个关键词
    keywords = ast.literal_eval(KEYWORDS)
    has_keyword = any(keyword in text for keyword in keywords)

    # 两个条件都满足才返回 True
    return has_tracking_or_code and has_keyword


def extract_express(input_str):
    """
    :param input_str:
    :return: ['319295288948927', '319295384033549', '319295908481368', '9402656067978', '9494054631545', '拦截']
    """
    # 匹配运单号（字母数字组合）和可选的汉字部分
    pattern = r'([A-Za-z]*\d+[A-Za-z\d#]*)\s*([\u4e00-\u9fa5]*)'
    matches = re.findall(pattern, input_str)

    results = []
    for match in matches:
        # 运单号部分
        express_num = match[0].strip()
        # 汉字部分
        chinese_part = match[1].strip()

        if express_num:
            # 如果运单号长度大于11位或者包含字母等（根据需求调整）
            if len(express_num) > 11:
                results.append(express_num)
            # 如果有汉字部分，也添加到结果中
            if chinese_part:
                results.append(chinese_part)
    return results


# 调用方法
# data = """
#  319295288948927 \n 319295384033549 \n 319295908481368 \n 9402656067978 \n 9494054631545 拦截
# """
# result = extract_express(data)
# print(result)
# print(len(result))
