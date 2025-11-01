import json
from dingtalk.api_handler import send_channel_notifications
from crawler.fetcher import get_latest_info
from crawler.config import SITES_FILE
from database.database import initialize_db, get_all_channels, add_new_notification, generate_fingerprint, is_notification_new

def load_json(path, default):
    try:
        return json.load(open(path, "r", encoding="utf-8"))
    except:
        return default

def process_and_notify():
    """执行完整的定时爬取、去重和推送流程。"""
    
    # 1. 加载新的结构化配置
    sites_config = load_json(SITES_FILE, [])
    
    # 2. 初始化数据库并导入配置
    print("--- 1. 初始化数据库及配置导入 ---")
    initialize_db(sites_config)

    # 3. 从数据库加载所有爬取任务（Channels）
    channels = get_all_channels()
    print(f"--- 2. 爬取任务开始 (共 {len(channels)} 个栏目) ---")
    
    total_new_items = 0

    for channel in channels:
        channel_id = channel['channel_id']
        site_name = channel['site_name']
        channel_name = channel['channel_name']
        
        print(f"正在爬取: [{site_name}] - {channel_name}...")

        # 4. 调用爬虫模块获取数据
        all_items = get_latest_info(channel)

        # 5. 核心：去重检查和推送数据准备
        new_items = []
        for item in all_items:
            fingerprint = generate_fingerprint(item["title"], item["link"])
            
            if is_notification_new(fingerprint):
                # 找到新通知，推送到列表，并立即写入数据库，标记为已处理
                new_items.append(item)
                add_new_notification(channel_id, item) 
                total_new_items += 1
        
        if new_items:
            # 6. 推送消息：调用我们新的、支持 Channel 的推送函数
            send_channel_notifications(
                channel_name=channel_name,
                site_name=site_name,
                new_notifications=new_items
            )
            print(f"    ✅ 推送 {len(new_items)} 条。")
        else:
            print(f"    无更新。")
    
    print(f"--- 任务完成。共发现和推送 {total_new_items} 条新通知 ---")
    
# 🚨 移除 if __name__ == "__main__": 块，让它成为一个纯模块供 main.py 导入