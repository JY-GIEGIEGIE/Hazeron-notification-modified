def format_message(site_name, channel_name, items):
    """
    根据抓取的通知生成钉钉推送消息文本
    :param site_name: 网站名称
    :param channel_name：子栏目名称
    :param items: [{'title': 'xxx', 'link': 'xxx', 'date': 'xxx'}, ...]
    """
    lines = [f"【{site_name}】-【{channel_name}】有新的通知：\n"]
    for item in items:
        lines.append(f"- 【{item['date']}】 {item['title']}\n  {item['link']}")
    return "\n".join(lines)