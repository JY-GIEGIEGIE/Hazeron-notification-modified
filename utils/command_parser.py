from typing import Dict, Any, Tuple
import re

def parse_command(raw_text: str) -> Tuple[str, Dict[str, Any]]:
    """
    从钉钉回调消息的原始文本中解析出命令和参数。
    此版本仅进行通用的文本清理和分割，不进行参数的语义识别。
    
    :param raw_text: 钉钉消息体中提取的原始文本内容。
    :return: 一个包含 (command, args) 的元组。
             - command: 识别出的标准化命令字符串（小写）。
             - args: 包含通用参数的字典。
    """
    
    # 1. 清理 @机器人 提及
    # 匹配并移除开头的 @提及
    cleaned_text = re.sub(r'^@\S+\s*', '', raw_text).strip()

    if not cleaned_text:
        # 仅提及机器人，没有发送命令
        return "default", {}

    # 2. 分割命令和参数
    parts = cleaned_text.split(maxsplit=1)
    
    # 提取命令，并转换为小写进行标准化
    command = parts[0].lower()
    
    # 提取参数文本
    param_text = parts[1].strip() if len(parts) > 1 else ""
    
    args: Dict[str, Any] = {}

    # 3. 简化：只将剩余的文本作为通用的 'param_str' 返回
    
    # 只有当参数文本非空时，才添加到 args 中
    if param_text:
        args['param_str'] = param_text

    # 对于不需要参数的命令（如 'help'），即使有额外文本，也可以忽略或进一步处理
    
    return command, args

# ----------------------------------------------------------------------
# 接口说明：现在 message_handler.py 负责语义识别
# ----------------------------------------------------------------------
"""
# 示例调用 (在 dingtalk/message_handler.py 中使用):

raw_msg = "@Hazeron search 最新教程"
command, args = parse_command(raw_msg)
# command -> 'search'
# args    -> {'param_str': '最新教程'}

# message_handler.py 现在进行语义识别：
if command == "search":
    keyword = args.get('param_str') 
    # 调用 search_service.execute_query(keyword)

"""