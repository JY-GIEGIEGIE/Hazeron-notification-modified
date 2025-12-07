# dingtalk/message_handler.py

import asyncio
from typing import Dict, Any, List

# 导入所有依赖的服务模块
from utils import command_parser
from services import search_service
from dingtalk import message_formatter 

# ----------------------------------------------------------------------
# 核心业务协调接口
# ----------------------------------------------------------------------

async def handle_user_command(message: Dict[str, Any]) -> str:
    """
    处理用户消息的核心业务协调函数。
    这是唯一被 dingtalk/stream_handler.py 调用的函数。
    
    :param message: 包含 text, sender_nick, conversation_id 等信息的字典。
    :return: 机器人将回复给用户的最终字符串。
    """
    
    raw_text = message.get('text', '')
    sender_nick = message.get('sender_nick', '用户')
    
    # 1. 解析指令：调用 command_parser 模块
    command, args = command_parser.parse_command(raw_text)
    
    try:
        if command == "search":
            # 语义识别：将通用的 'param_str' 映射为 'keyword'
            keyword = args.get('param_str')
            
            if not keyword:
                # 关键词缺失，回复帮助信息
                return message_formatter.format_help(sender_nick)
            
            # 2. 调用搜索服务 (核心逻辑接口)
            # 替换了所有模拟代码，直接调用并 await 真实的异步服务函数
            results: List[Dict[str, Any]] = await search_service.execute_query(keyword)
            
            # 3. 格式化回复：调用 message_formatter 模块
            if results:
                return message_formatter.format_search_results(results, keyword)
            else:
                return message_formatter.format_search_not_found(keyword)
        
        elif command == "help":
            return message_formatter.format_help(sender_nick)

        # 4. 默认/未知命令回复
        elif command == "default":
             return message_formatter.format_default_response(sender_nick)
        else :
            return message_formatter.format_command_error(sender_nick, command)

    except Exception as e:
        # 捕获服务调用中的任何意外错误
        # 实际项目中应记录到 logger 中
        return message_formatter.format_error(e)