def format_message(site_name, items):
    """
    根据抓取的通知生成钉钉推送消息文本
    :param site_name: 网站名称
    :param items: [{'title': 'xxx', 'link': 'xxx', 'date': 'xxx'}, ...]
    """
    lines = [f"【{site_name}】有新的通知：\n"]
    for item in items:
        lines.append(f"- 【{item['date']}】 {item['title']}\n  {item['link']}")
    return "\n".join(lines)