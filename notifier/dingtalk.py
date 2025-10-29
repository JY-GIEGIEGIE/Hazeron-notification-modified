import time, hmac, hashlib, base64, urllib.parse, requests

def send_dingtalk_msg(webhook, msg, secret=None):
    url = webhook
    if secret:
        timestamp = str(round(time.time() * 1000))
        string_to_sign = f"{timestamp}\n{secret}"
        hmac_code = hmac.new(secret.encode(), string_to_sign.encode(), digestmod=hashlib.sha256).digest()
        sign = urllib.parse.quote_plus(base64.b64encode(hmac_code))
        url += f"&timestamp={timestamp}&sign={sign}"
    payload = {"msgtype": "text", "text": {"content": msg}}
    requests.post(url, json=payload)
