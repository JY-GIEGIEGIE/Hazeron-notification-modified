from typing import Dict, Any, List
from . import html_handler  
from . import api_handler

def get_latest_info(site: Dict[str, Any]) -> List[Dict[str, str]]:
    """
    根据站点的配置（特别是 'mode' 字段），调用相应的处理器（Handler）来抓取数据。
    
    :param site: JSON 配置中单个网站的字典。
    :return: 包含字典（title, link, date）的列表。
    """
    
    # 默认模式为 'html'，以兼容没有明确 mode 字段的旧配置
    mode = site.get("mode", "html").lower() 
    site_name = site.get("name", "Unknown Site")

    print(f"--- 正在处理站点: {site_name} (模式: {mode}) ---")

    if mode == "html":
        # HTML 模式: 调用 HTML 解析处理器
        try:
            return html_handler.get_info_from_html(site)
        except Exception as e:
            print(f"处理 {site_name} (HTML模式) 时发生错误: {e}")
            return []
            
    elif mode == "api":
        # API 模式: 调用 JSON API 处理器
        try:
            return api_handler.get_info_from_api(site)
        except Exception as e:
            print(f"处理 {site_name} (API模式) 时发生错误: {e}")
            return []
            
    else:
        # 未知模式处理
        print(f"错误: 站点 {site_name} 配置了未知的抓取模式: {mode}")
        return []