from typing import Dict, Any, List
from . import html_handler
from . import api_handler

def get_latest_info(channel_task: Dict[str, Any]) -> List[Dict[str, str]]:
    """
    根据栏目（Channel）的配置，调用相应的处理器（Handler）来抓取数据。
    
    :param channel_task: 包含完整配置的单个栏目任务字典（来自数据库）。
    :return: 包含字典（title, link, date）的列表。
    """
    
    # 获取必要的元数据
    # 这里的 'mode' 和 'site_name'/'channel_name' 都是从数据库返回的扁平化字典中直接获取
    mode = channel_task.get("mode", "html").lower() 
    site_name = channel_task.get("site_name", "Unknown Site")
    channel_name = channel_task.get("channel_name", "Unknown Channel") # 新增获取 channel_name
    
    # 日志增强，显示任务的全名
    print(f"--- 正在处理任务: [{site_name}] {channel_name} (模式: {mode}) ---")

    if mode == "html":
        # HTML 模式: 调用 HTML 解析处理器
        try:
            # 将完整的任务字典传递给 Handler
            return html_handler.get_info_from_html(channel_task)
        except Exception as e:
            print(f"处理 [{site_name}] {channel_name} (HTML模式) 时发生错误: {e}")
            return []
            
    elif mode == "api":
        # API 模式: 调用 JSON API 处理器
        try:
            # 将完整的任务字典传递给 Handler
            return api_handler.get_info_from_api(channel_task)
        except Exception as e:
            print(f"处理 [{site_name}] {channel_name} (API模式) 时发生错误: {e}")
            return []
            
    else:
        # 未知模式处理
        print(f"错误: 栏目 [{site_name}] {channel_name} 配置了未知的抓取模式: {mode}")
        return []