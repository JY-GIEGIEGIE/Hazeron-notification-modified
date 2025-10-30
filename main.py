import json
import os
from crawler.fetcher import get_latest_info
from utils.formatter import format_message
from notifier.dingtalk import send_dingtalk_msg
from repo.database import initialize_db, get_all_channels, add_new_notification, generate_fingerprint, is_notification_new
from crawler.config import load_json, load_secret, save_json
from crawler.config import SECRET_FILE, DATA_FILE, SITES_FILE


def main():
    webhook, secret, _, _ = load_secret(SECRET_FILE)
    
    # 1. 加载新的结构化配置
    sites_config = load_json(SITES_FILE, [])
    
    # 2. 初始化数据库并导入配置
    # 这一步会创建 Channel/Notification 表，并更新 Channel 表的配置
    print("--- 1. 初始化数据库及配置导入 ---")
    initialize_db(sites_config)

    # 3. 从数据库加载所有爬取任务（Channels）
    # 每一个 channel 包含完整的爬虫配置和唯一的 channel_id
    channels = get_all_channels()
    print(f"--- 2. 爬取任务开始 (共 {len(channels)} 个栏目) ---")
    
    total_new_items = 0

    for channel in channels:
        channel_id = channel['channel_id']
        site_name = channel['site_name']
        channel_name = channel['channel_name']
        
        print(f"正在爬取: [{site_name}] - {channel_name}...")

        # 4. 调用爬虫模块获取数据 (channel 现在包含所有配置)
        all_items = get_latest_info(channel) # 注意：这里 get_latest_info 的参数变了

        # 5. 核心：去重检查和推送
        new_items = []
        for item in all_items:
            fingerprint = generate_fingerprint(item["title"], item["link"])
            
            if is_notification_new(fingerprint):
                # 找到新通知，推送到列表，并立即写入数据库，标记为已处理
                new_items.append(item)
                add_new_notification(channel_id, item) 
                total_new_items += 1
        
        if new_items:
            # 6. 推送消息 (现在消息中可以包含 channel_name)
            msg = format_message(site_name, channel_name, new_items)
            send_dingtalk_msg(webhook, msg, secret)
            print(f"    ✅ 推送 {len(new_items)} 条。")
        else:
            print(f"    无更新。")
    
    print(f"--- 任务完成。共发现和推送 {total_new_items} 条新通知 ---")
    # 移除 save_json(DATA_FILE, last_state)，因为数据库已自动保存
    
if __name__ == "__main__":
    main()