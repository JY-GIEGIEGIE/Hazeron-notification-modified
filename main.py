import json
from crawler.fetcher import get_latest_info
from utils.formatter import format_message
from notifier.dingtalk import send_dingtalk_msg

SECRET_FILE = 'config/secret_config.json'
DATA_FILE = "storage/last_state.json"
SITES_FILE = "config/sites.json"

def load_secret(path) :
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
    try:
        return json.load(open(path, "r", encoding="utf-8"))
    except:
        return default

def save_json(path, data):
    json.dump(data, open(path, "w", encoding="utf-8"), ensure_ascii=False, indent=2)

def main():
    webhook, secret = load_secret(SECRET_FILE)
    sites = load_json(SITES_FILE, [])
    last_state = load_json(DATA_FILE, {})

    for s in sites:
        items = get_latest_info(s)
        old_items = last_state.get(s["name"], [])
        old_links = {i["link"] for i in old_items}

        new_items = [i for i in items if i["link"] not in old_links]

        if new_items:
            msg = format_message(s["name"], new_items)
            send_dingtalk_msg(webhook, msg, secret)
            last_state[s["name"]] = items
            print(f"{s['name']} 推送 {len(new_items)} 条。")
        else:
            print(f"{s['name']} 无更新。")

    save_json(DATA_FILE, last_state)

if __name__ == "__main__":
    main()
