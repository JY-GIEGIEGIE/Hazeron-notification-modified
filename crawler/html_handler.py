import requests
import re
from urllib.parse import urljoin
from bs4 import BeautifulSoup, Tag
from typing import Dict, Any, List
from ZJUWebVPN import ZJUWebVPNSession
from .config import load_secret
from .config import SECRET_FILE
# ====================================================================
# 辅助函数: 提取数据子模块 (保持不变)
# ====================================================================


def _extract_title(li: Tag, title_selector: str) -> str:
    """从列表项中提取标题。"""
    title = "N/A"
    content_element = li.select_one(title_selector) if title_selector else None

    if content_element:
        title_raw = content_element.text.strip()
        if title_raw:
            title = title_raw
    return title


def _extract_link(li: Tag, base_url: str, title_selector: str) -> str:
    """从列表项中提取并构造完整链接。"""
    link = "N/A"
    link_anchor = None
    
    content_element = li.select_one(title_selector) if title_selector else None

    if content_element:
        link_anchor = content_element.find_parent("a")

    # 2. 特殊情况：如果内容元素本身就是 <a> 标签
    if content_element and content_element.name == "a":
        link_anchor = content_element

    # 3. 兜底查找：在 li 内部直接找 <a> 标签
    if not link_anchor:
        link_anchor = li.select_one("a")

    # 4. 构造完整链接
    if link_anchor and link_anchor.get("href"):
        href = link_anchor.get("href")
        if href and not href.lower().startswith("javascript:"):
            link = urljoin(base_url, href)
        elif base_url:
            link = base_url
    elif base_url:
        link = base_url

    return link


def _extract_date(li: Tag, selectors: Dict[str, Any]) -> str:
    """从列表项中提取日期并进行格式化验证。"""
    date = "N/A"
    date_selector = selectors.get("date_selector")
    date_regex_config = selectors.get("date_regex", {})

    source_element = li.select_one(date_selector) if date_selector else li
    pattern = date_regex_config.get("pattern") if date_regex_config else None

    if pattern:
        format_str = date_regex_config.get("format") or "$1"
        source_html = str(source_element)
        match = re.search(pattern, source_html, re.IGNORECASE | re.DOTALL)

        if match:
            date_temp = format_str
            for i in range(1, len(match.groups()) + 1):
                date_temp = date_temp.replace(f"${i}", match.group(i))
            if date_temp.strip():
                date = date_temp.strip()

    else:
        date_text = source_element.text.strip()
        if date_text:
            date = date_text

    if date != "N/A":
        # 匹配 YYYY-MM-DD 格式
        date_match = re.search(r"(\d{4})[^\d](\d{1,2})[^\d](\d{1,2})[^\d]*", date)

        if date_match:
            year = date_match.group(1)
            month = date_match.group(2).zfill(2)
            day = date_match.group(3).zfill(2)
            date = f"{year}-{month}-{day}"
        else:
            # 尝试匹配 YYYY-MM 格式
            date_match_month = re.search(r"(\d{4})[^\d](\d{1,2})", date)
            if date_match_month:
                year = date_match_month.group(1)
                month = date_match_month.group(2).zfill(2)
                date = f"{year}-{month}-00"
            else:
                date = "N/A"

    return date


# ====================================================================
# 主功能函数: 从单个列表项中提取数据 (修正 base_url 键名)
# ====================================================================



def extract_data_from_li(li: Tag, html_config: Dict[str, Any], base_link_url: str) -> Dict[str, str]:
    """从单个列表项（li）中提取核心数据，组合调用三个辅助函数。"""

    selectors = html_config.get("selectors", {})
    # 使用从顶层任务字典中传入的 base_link_url
    title_selector = selectors.get("title_selector")

    title = _extract_title(li, title_selector)
    # 使用正确的 base_link_url 变量名
    link = _extract_link(li, base_link_url, title_selector)
    date = _extract_date(li, selectors)

    return {"title": title, "link": link, "date": date}


# ====================================================================
# 主处理器: HTML 模式入口 (核心修正)
# ====================================================================


def get_info_from_html(channel_task: Dict[str, Any]) -> List[Dict[str, str]]:
    """根据配置获取并解析 HTML 页面，支持多 URL 爬取。"""
    
    _, _, webvpn_name, webvpn_secret = load_secret(SECRET_FILE)
    ses = ZJUWebVPNSession(webvpn_name, webvpn_secret)
    # 1. 从扁平化任务字典中获取所需配置
    html_config = channel_task.get("html_config", {})
    
    # max_count 和 base_link_url 是扁平化字段，直接在顶层
    max_count = channel_task.get("max_count", 5) 
    base_link_url = channel_task.get("base_link_url", "") # 【修正】使用正确的键名
    
    # url_list 是完整的 URL 列表，来自 JSON 内部
    url_list = channel_task.get("url_list", []) 

    site_name = channel_task.get("site_name", "Unknown")
    channel_name = channel_task.get("channel_name", "Unknown")
    
    # 2. URL 配置验证
    if not url_list or not isinstance(url_list, list):
        print(f"错误: 栏目 [{site_name}] {channel_name} 的 url_list 配置无效。")
        return []

    list_selector = html_config.get("selectors", {}).get("list_selector")
    if not list_selector:
        print(f"错误: 栏目 [{site_name}] {channel_name} 缺少 list_selector。")
        return []

    items: List[Dict[str, str]] = []
    
    # 3. 循环处理每一个 URL (支持多 URL 爬取)
    for current_url in url_list:
        if not current_url: continue
        
        print(f"  -> 正在处理 HTML 页面: {current_url}")

        # 请求和解析 HTML
        # try:
        r = ses.get(current_url, timeout=10)
        r.encoding = r.apparent_encoding if r.apparent_encoding else "utf-8"
        soup = BeautifulSoup(r.text, "html.parser")
        # except ses.exceptions.RequestException as e:
        #     print(f"请求 {current_url} 失败: {e}")
        #     continue

        # 3. 提取数据
        current_item_count = 0
        for li in soup.select(list_selector):
            # 传递 html_config 和 base_link_url 给提取函数
            info = extract_data_from_li(li, html_config, base_link_url)
            
            if info["title"] != "N/A":
                items.append(info)
                current_item_count += 1

            # 在处理完一个 URL 后，或达到 max_count 时停止
            if current_item_count >= max_count:
                break
                
    return items
