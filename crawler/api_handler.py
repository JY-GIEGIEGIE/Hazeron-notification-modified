import requests
import re
import json
from typing import Dict, Any, List


def get_info_from_api(site: Dict[str, Any]) -> List[Dict[str, str]]:
    """
    根据 API 配置从 JSON 接口提取信息。

    :param site: JSON 配置中单个 API 网站的字典。
    :return: 包含字典（title, link, date）的列表。
    """
    api_config = site.get("api_config", {})
    api_url = api_config.get("url")
    # 读取用于链接拼接的基础 URL
    base_link_url = api_config.get("base_link_url") 
    fields_map = api_config.get("fields_map", {})
    # 读取数据列表的路径
    data_path = api_config.get("data_path", []) 
    
    if not api_url or not fields_map or not base_link_url:
        print(f"API 配置不完整（URL, base_link_url 或 fields_map 缺失），跳过站点: {site.get('name', 'Unknown Site')}")
        return []

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Accept': 'application/json'
    }

    try:
        r = requests.get(api_url, headers=headers, timeout=10)
        r.raise_for_status() 
        api_data = r.json()
    except requests.exceptions.RequestException as e:
        print(f"API 请求 {api_url} 失败: {e}")
        return []
    except json.JSONDecodeError:
        print(f"API 响应不是有效的 JSON: {api_url}")
        return []

    # --- 遍历数据路径 ---
    data_list = api_data
    try:
        # 根据 data_path (例如: ["data", "records"]) 逐级向下查找实际的列表数据
        for key in data_path:
            # 使用 .get() 配合 is not None 确保安全性，但对于列表路径通常用 [] 查找
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
    items: List[Dict[str, str]] = []
    max_count = site.get("max_count", 5)

    for item_data in data_list:
        if not isinstance(item_data, dict):
            continue # 跳过非字典格式的数据

        # 提取字段的 API 键名
        title_api_key = fields_map.get("title", "title")
        date_api_key = fields_map.get("date", "publishTime")
        # 使用 link_key
        link_api_key = fields_map.get("link_key", "newsId") 
        
        # 1. 提取数据
        title = str(item_data.get(title_api_key, "N/A"))
        raw_date = item_data.get(date_api_key, "N/A")
        link_value = item_data.get(link_api_key, None)
        
        # 2. 清理日期格式 (兼容 ISO 8601 'T' 分割和普通空格分割)
        date = "N/A"
        date_str = str(raw_date).strip() # 清理首尾空白
        
        if date_str != "N/A":
            if 'T' in date_str:
                # 优先处理 ISO 8601 格式，以 'T' 分割
                extracted_date_part = date_str.split('T')[0]
            elif ' ' in date_str:
                # 处理传统 YYYY-MM-DD HH:MM:SS 格式，以空格分割
                extracted_date_part = date_str.split(' ')[0]
            else:
                # 可能是已经是 YYYY-MM-DD 格式，或者其他无法自动分割的格式
                extracted_date_part = date_str
            
            # 最终验证：确保提取到的部分看起来像一个日期 (YYYY-MM-DD 或 YYYY/MM/DD)
            # 只需要 re 模块，无需导入 datetime 即可完成这个任务
            if re.match(r'^\d{4}[-/]\d{2}[-/]\d{2}$', extracted_date_part):
                 date = extracted_date_part
            # 否则，date 保持为 "N/A"
        
        # 3. 构造链接 (使用 link_key 提取的值和 base_link_url)
        link = "N/A"

        # --- 场景 1: base 和 value 都存在，进行拼接 (最常见情况) ---
        if base_link_url and link_value is not None:
            link = f"{base_link_url}{link_value}"

        # --- 场景 3: 只有 value 存在 (API 返回完整链接或路径) ---
        # 此时 base_link_url 为 None 或空字符串。我们将 link_value 视为完整的链接。
        # 注意：需要确保 base_link_url 不存在，否则会触发上一个 if
        elif link_value is not None and not base_link_url:
            link = str(link_value) # 将 link_value 视为完整链接

        # --- 场景 2: 只有 base 存在 (没有详情页，链接就是列表/入口页) ---
        # 此时 link_value 为 None。
        elif link_value is None and base_link_url:
            link = base_link_url
                
            # 确保标题是存在的
            if title == "N/A":
                continue

        items.append({"title": title, "link": link, "date": date})

        if len(items) >= max_count:
            break
            
    return items