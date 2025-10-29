import json

SECRET_FILE = "config/secret_config.json"
DATA_FILE = "storage/last_state.json"
SITES_FILE = "config/sites.json"


def load_secret(path):
    try:
        with open(path, "r", encoding="utf-8") as f:
            secrets = json.load(f)
            webhook = secrets["WEBHOOK"]
            secret = secrets["SECRET"]
            webvpn_name = secrets["WEBVPN_NAME"]
            webvpn_secret = secrets["WEBVPN_SECRET"]
        return webhook, secret, webvpn_name, webvpn_secret
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
