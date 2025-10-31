# services/message_formatter.py

from typing import List, Dict, Any

def format_search_results(results: List[Dict[str, Any]], keyword: str) -> str:
    """
    将搜索结果列表格式化为钉钉 Markdown 消息。
    :param results: 搜索结果字典列表，预期包含 'title', 'link', 'date', 'site_name', 'channel_name'。
    :param keyword: 用户输入的关键词。
    :return: 格式化后的 Markdown 字符串。
    """
    
    # 标题使用三级标题，突出关键词
    header = f"### 🔎 配置搜索结果：`{keyword}`\n"
    
    # 找到的总数
    total_count = len(results)
    
    # 限制展示数量，避免消息过长，钉钉消息体建议在 1000 字符内
    display_limit = 10
    display_results = results[:display_limit]
    
    content_list = []
    
    for i, item in enumerate(display_results):
        title = item.get('title', '无标题')
        link = item.get('link', '#')
        date = item.get('date', '未知日期')
        site_name = item.get('site_name', '未知站点')
        channel_name = item.get('channel_name', '未知栏目')
        
        # 格式化每一条记录：使用无序列表和引用块
        item_str = (
            f"\n\n---" # 分隔线
            f"\n\n#### {i+1}. [{title}]({link})" # 序号和链接标题
            f"\n\n> **站点/栏目：** `{site_name} / {channel_name}`"
            f"\n\n> **发布时间：** `{date}`"
        )
        content_list.append(item_str)
        
    # 底部总结和提示
    summary = f"\n\n共找到 **{total_count}** 条记录。"
    
    footer = ""
    if total_count > display_limit:
        footer = f"\n\n> 💡 结果过多，仅展示前 {display_limit} 条记录。"
        
    # 整合所有部分
    return header + summary + "".join(content_list) + footer


def format_search_not_found(keyword: str) -> str:
    """
    格式化搜索无结果的回复，并提示高级搜索用法。
    """
    return (
        f"### 🤷‍♂️ 搜索无果\n\n"
        f"抱歉，没有找到与 **`{keyword}`** 相关的通知。\n\n"
        f"> **💡 高级搜索提示：**\n"
        f"> 尝试使用 **`AND`**、**`OR`**、**`NOT`** 进行布尔组合搜索，并使用 **英文圆括号 `()`** 嵌套逻辑。\n"
        f"> **示例：** `search (专业 AND 同意) OR 智能化学`"
    )


def format_help(sender_nick: str) -> str:
    """
    格式化帮助/用法提示信息，使用 Markdown 引用突出显示，并包含用户昵称。
    """
    return (
        f"### 👋 您好，{sender_nick}！这是 Hazeron 帮助\n\n"
        f"> **Hazeron** 致力于帮您快速查找和订阅通知信息。您可以通过以下命令与我互动。\n\n"
        f"**快速命令参考：**\n"
        f"* `help`：显示此帮助信息。\n"
        f"* `search [关键词]`：在历史通知中搜索记录。\n\n"
        f"**🔍 高级搜索用法：**\n"
        f"搜索支持 **中文智能分词** 和 **布尔逻辑组合**。\n"
        f"* **操作符：** `AND`, `OR`, `NOT` (大写)\n"
        f"* **分组：** 使用圆括号 `()` 来嵌套搜索逻辑。\n"
        f"* **示例：** `search (系统 AND 教程) OR (配置 NOT 视频)`"
    )


def format_default_response(sender_nick: str) -> str:
    """
    格式化默认或欢迎回复，引导用户使用高级搜索。
    """
    return (
        f"### 👋 欢迎，{sender_nick}！\n\n"
        f"我是 **Hazeron**，致力于帮您快速查找和订阅通知信息。\n\n"
        f"**您可以尝试：**\n"
        f"* 输入 `search [关键词]` 进行搜索。支持 `AND/OR/NOT` 高级布尔查询。\n"
        f"* 输入 `help` 查看所有可用命令和搜索示例。"
    )

def format_command_error(sender_nick: str, command: str) -> str:
    """
    命令错误时的默认回复
    """
    return (
        f"### ❓ 命令无法识别\n\n"
        f"抱歉，{sender_nick}！我无法理解命令：**`{command}`**。\n\n"
        f"> 请检查拼写，或输入 `help` 查看支持的命令。"
    )


def format_error(error_message: str) -> str:
    """
    格式化内部错误提示。
    """
    return (
        f"### 🚨 系统内部错误\n\n"
        f"非常抱歉，在处理您的请求时系统发生了一个意外错误。\n\n"
        f"> **错误详情：** `{error_message}`\n\n"
        f"> 请联系管理员或稍后重试。"
    )