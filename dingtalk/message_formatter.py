# services/message_formatter.py

from typing import List, Dict, Any

def format_search_results(results: List[Dict[str, Any]], keyword: str) -> str:
    """
    将搜索结果列表格式化为钉钉 Markdown 消息。
    """
    
    # 标题使用 Markdown 粗体
    header = f"### 🔍 搜索结果: `{keyword}`\n"
    content_list = []
    
    for i, item in enumerate(results[:5]): # 限制展示数量，避免消息过长
        title = item.get('title', '无标题')
        link = item.get('link', '#')
        date = item.get('date', '未知日期')
        
        # 格式化每一条记录
        item_str = (
            f"\n---\n"
            f"**{i+1}. [{title}]({link})**\n"
            f"> 发布日期: {date}"
        )
        content_list.append(item_str)
        
    footer = "\n\n> 仅展示前5条结果。" if len(results) > 5 else ""
    
    return header + "".join(content_list) + footer


def format_not_found(keyword: str) -> str:
    """
    格式化搜索无结果的回复。
    """
    return f"🤷‍♂️ 抱歉，没有找到与 **{keyword}** 相关的配置信息。请尝试更换关键词。"


def format_help(message: str) -> str:
    """
    格式化帮助/用法提示信息，使用 Markdown 引用突出显示。
    """
    return f"💡 帮助信息:\n\n> {message}"


def format_default_response(sender_nick: str) -> str:
    """
    格式化默认或欢迎回复。
    """
    # 纯文本回复
    return f"你好，{sender_nick}！我是Hazeron。请输入 'search [关键词]' 或 'help' 来与我互动。"

def format_command_error(sender_nick: str, command: str) -> str:
    """
    命令错误时的默认回复
    """
    return f"抱歉，{sender_nick}！命令 '{command}' 无法识别。请输入 'help'。"


def format_error(error_message: str) -> str:
    """
    格式化内部错误提示。
    """
    # 报警信息使用 Markdown 颜色突出
    return f"🚨 **系统错误** 🚨\n\n> 发生了一个内部错误：{error_message}"