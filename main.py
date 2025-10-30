import json
import os # 需要导入os来构建安全的路径
from crawler.fetcher import get_latest_info
from utils.formatter import format_message
from notifier.dingtalk import send_dingtalk_msg
# --- 导入新的数据库模块 ---
from repo.database import initialize_db, get_all_channels, add_new_notification, generate_fingerprint, is_notification_new

# --- 文件路径常量更新 ---
SECRET_FILE = 'config/secret_config.json'
SITES_FILE = "config/test.json"
# 移除 DATA_FILE，因为它被数据库取代了

def load_secret(path):
    # ... (保持不变，用于加载 SECRET 和 WEBHOOK) ...
    try:
        with open(path, 'r', encoding='utf-8') as f:
            secrets = json.load(f)
            webhook = secrets["WEBHOOK"] 
            secret = secrets["SECRET"]
        return webhook, secret
    except Exception as e:
        print(f"致命错误：加载关键配置 '{SECRET_FILE}' 时发生错误。")
        print(f"详细信息: {e}")
        exit(1)


def load_json(path, default):
    """加载配置JSON文件"""
    try:
        # 确保使用 os.path.join 来构建路径，提高可移植性
        return json.load(open(os.path.join(os.path.dirname(__file__), path), "r", encoding="utf-8"))
    except FileNotFoundError:
        print(f"警告：配置文件 '{path}' 未找到，使用默认值。")
        return default
    except Exception as e:
        print(f"加载配置文件 '{path}' 错误: {e}")
        return default


def main():
    webhook, secret = load_secret(SECRET_FILE)
    
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