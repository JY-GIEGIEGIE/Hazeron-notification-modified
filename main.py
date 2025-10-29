from crawler.fetcher import get_latest_info
from utils.formatter import format_message
from notifier.dingtalk import send_dingtalk_msg
from crawler.config import load_json, load_secret, save_json
from crawler.config import SECRET_FILE, DATA_FILE, SITES_FILE


def main():
    webhook, secret, _, _ = load_secret(SECRET_FILE)
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
