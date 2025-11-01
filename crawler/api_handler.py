import requests
import re
import json
from typing import Dict, Any, List
from ZJUWebVPN import ZJUWebVPNSession
from crawler.config import ENABLE_WEBVPN
from config.secret_config import WEBVPN_NAME, WEBVPN_SECRET


def get_info_from_api(channel_task: Dict[str, Any]) -> List[Dict[str, str]]:
    """
    根据 API 配置从 JSON 接口提取信息。

    :param channel_task: 包含完整配置的单个栏目任务字典（来自数据库）。
    :return: 包含字典（title, link, date）的列表。
    """
    # 根据全局配置和每个 channel 的可选覆盖决定使用哪种会话
    use_webvpn = channel_task.get("use_webvpn", ENABLE_WEBVPN)
    if use_webvpn:
        ses = ZJUWebVPNSession(WEBVPN_NAME, WEBVPN_SECRET)
    else:
        ses = requests.Session()
    api_config = channel_task.get("api_config", {})
    max_count = channel_task.get("max_count", 5) 
    base_link_url = channel_task.get("base_link_url", "") # 【修正】从顶层获取
    url_list = channel_task.get("url_list", []) # 【修正】使用 url_list

    site_name = channel_task.get("site_name", "Unknown")
    channel_name = channel_task.get("channel_name", "Unknown")
    fields_map = api_config.get("fields_map", {})
    data_path = api_config.get("data_path", []) 
    
    # 2. 基础配置验证
    if not url_list or not isinstance(url_list, list):
        print(f"错误: 栏目 [{site_name}] {channel_name} 的 url_list 配置无效。")
        return []

    if not fields_map or not base_link_url:
        print(f"API 配置不完整（base_link_url 或 fields_map 缺失），跳过栏目: {channel_name}")
        return []

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Accept": "application/json",
    }

    items: List[Dict[str, str]] = []

    # 3. 循环处理每一个 API URL (支持多 URL 爬取)
    for api_url in url_list:
        current_item_count = 0
        if not api_url: continue
        
        print(f"  -> 正在处理 API 接口: {api_url}")
        
        # 请求 API
        try:
            r = ses.get(api_url, headers=headers, timeout=10)
            r.raise_for_status() 
            api_data = r.json()
        except requests.exceptions.RequestException as e:
            print(f"API 请求 {api_url} 失败: {e}")
            continue
        except json.JSONDecodeError:
            print(f"API 响应不是有效的 JSON: {api_url}")
            continue

        # --- 遍历数据路径 ---
        data_list = api_data
        try:
            # 根据 data_path (例如: ["data", "records"]) 逐级向下查找实际的列表数据
            for key in data_path:
                if isinstance(data_list, dict):
                    data_list = data_list.get(key)
                elif isinstance(data_list, list) and isinstance(key, int):
                    data_list = data_list[key]
                else:
                    raise KeyError(f"无法从当前级别 {type(data_list)} 中找到键/索引: {key}")
            
            if not isinstance(data_list, list):
                print(f"API 路径 {data_path} 未指向一个有效的列表。")
                data_list = []
        except Exception as e:
            print(f"解析 API 响应结构失败 (data_path: {data_path}, 错误: {e})")
            data_list = []

        # --- 提取字段并构造链接 ---

        for item_data in data_list:
            if not isinstance(item_data, dict):
                continue

            # 提取字段的 API 键名
            title_api_key = fields_map.get("title", "title")
            date_api_key = fields_map.get("date", "publishTime")
            link_api_key = fields_map.get("link_key", "newsId") 
            
            # 1. 提取数据
            title = str(item_data.get(title_api_key, "N/A"))
            raw_date = item_data.get(date_api_key, "N/A")
            link_value = item_data.get(link_api_key, None)
            
            # 2. 清理日期格式
            date = "N/A"
            date_str = str(raw_date).strip()
            
            if date_str != "N/A":
                if 'T' in date_str:
                    extracted_date_part = date_str.split('T')[0]
                elif ' ' in date_str:
                    extracted_date_part = date_str.split(' ')[0]
                else:
                    extracted_date_part = date_str
                
                if re.match(r'^\d{4}[-/]\d{2}[-/]\d{2}$', extracted_date_part):
                    date = extracted_date_part
            
            # 3. 构造链接 (使用 link_key 提取的值和 base_link_url)
            link = "N/A"

            # --- 场景 1: base 和 value 都存在，进行拼接 (最常见情况) ---
            if base_link_url and link_value is not None:
                link = f"{base_link_url}{link_value}"

            # --- 场景 3: 只有 value 存在 (API 返回完整链接或路径) ---
            elif link_value is not None and not base_link_url:
                link = str(link_value)

            # --- 场景 2: 只有 base 存在 (没有详情页，链接就是列表/入口页) ---
            elif link_value is None and base_link_url:
                link = base_link_url
                if title == "N/A":
                    continue

            items.append({"title": title, "link": link, "date": date})
            current_item_count += 1

            if current_item_count >= max_count:
                return items
    
    return items
