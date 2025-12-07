# services/search_service.py
import asyncio
from typing import Dict, Any, List

# 导入 database.py 中的搜索函数
from database import search_db

async def execute_query(keyword: str, limit: int = 10) -> List[Dict[str, Any]]:
    """
    异步函数：安全地执行数据库搜索。
    将同步的 database.py 调用移至线程池，防止阻塞 asyncio 事件循环。
    
    :param keyword: 用户输入的搜索关键词。
    :param limit: 限制返回结果的数量。
    :return: 包含搜索结果的字典列表。
    """
    
    if not keyword or not keyword.strip():
        return []
    
    # 核心步骤：获取当前事件循环
    loop = asyncio.get_event_loop()
    
    # 使用 loop.run_in_executor 将同步的数据库调用放入默认的线程池中执行。
    # 这样，当线程在等待 I/O 时，主线程可以继续处理其他事件。
    try:
        results = await loop.run_in_executor(
            None, 
            search_db.search_notifications_sync, 
            keyword
    )
        
        # 结果结构示例：
        # [{'title': '...', 'link': '...', 'date': '...', 'site_name': '...', 'channel_name': '...'}, ...]
        return results
        
    except Exception as e:
        # 实际项目中应使用 logging 记录错误
        print(f"[ERROR] Database search failed in executor: {e}")
        return []