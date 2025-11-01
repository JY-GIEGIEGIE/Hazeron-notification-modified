import json
import time
from typing import List, Dict, Any

# 导入配置和格式化器
from config.secret_config import (
    CLIENT_ID, CLIENT_SECRET, 
    DINGTALK_ROBOT_CODE, DINGTALK_CONVERSATION_ID
)
from dingtalk.message_formatter import format_channel_update_markdown

# 钉钉 SDK 导入
from alibabacloud_dingtalk.robot_1_0.client import Client as DingTalkRobotClient
from alibabacloud_dingtalk.robot_1_0 import models as dingtalk_robot_models
from alibabacloud_dingtalk.oauth2_1_0.client import Client as DingTalkOAuthClient
from alibabacloud_dingtalk.oauth2_1_0 import models as dingtalk_oauth_models
from alibabacloud_tea_openapi import models as open_api_models
from alibabacloud_tea_util.client import Client as UtilClient
from alibabacloud_tea_util import models as util_models

# ======================================================================
# 1. 动态 Access Token 管理
# ======================================================================

_CACHED_ACCESS_TOKEN = None
_TOKEN_EXPIRE_TIME = 0

def _get_dingtalk_oauth_client() -> DingTalkOAuthClient:
    """初始化 OAuth 客户端。"""
    config = open_api_models.Config()
    config.protocol = 'https'
    config.region_id = 'central'
    return DingTalkOAuthClient(config)

def get_access_token() -> str:
    """
    获取/刷新 Access Token。
    """
    global _CACHED_ACCESS_TOKEN, _TOKEN_EXPIRE_TIME
    
    if _CACHED_ACCESS_TOKEN and time.time() < _TOKEN_EXPIRE_TIME - 10:
        return _CACHED_ACCESS_TOKEN

    print("[DingTalk] Access Token 过期或首次获取，正在请求新的令牌...")
    
    oauth_client = _get_dingtalk_oauth_client()
    get_access_token_request = dingtalk_oauth_models.GetAccessTokenRequest(
        app_key=CLIENT_ID,
        app_secret=CLIENT_SECRET
    )
    
    try:
        response = oauth_client.get_access_token(get_access_token_request)
        
        token = response.body.access_token
        expires_in = response.body.expire_in
        
        _CACHED_ACCESS_TOKEN = token
        _TOKEN_EXPIRE_TIME = time.time() + expires_in
        
        print(f"[DingTalk] 成功获取新的 Access Token，有效期 {expires_in} 秒。")
        return token
        
    except Exception as err:
        print("[DingTalk ERROR] 无法获取 Access Token，请检查配置。")
        raise ConnectionError("无法连接钉钉 OAuth 服务获取令牌。")

# dingtalk/api.py (修正后的核心推送函数)

# ... (前面的导入保持不变)
# 导入新的格式化函数
from dingtalk.message_formatter import format_channel_update_markdown

def _create_dingtalk_robot_client() -> DingTalkRobotClient:
    """初始化机器人客户端。"""
    config = open_api_models.Config()
    config.protocol = 'https'
    config.region_id = 'central'
    return DingTalkRobotClient(config)

DINGTALK_ROBOT_CLIENT = _create_dingtalk_robot_client()

def send_channel_notifications(
    channel_name: str, 
    site_name: str, 
    new_notifications: List[Dict[str, Any]]
):
    """
    核心推送函数：向钉钉群组发送某个 Channel 的新通知汇总消息。
    
    Args:
        channel_name: 分栏名称 (如：公示专区)
        site_name: 网站名称 (如：云峰学园)
        new_notifications: 属于该 Channel 的新通知字典列表。
    """
    if not new_notifications:
        return

    try:
        access_token = get_access_token()
    except ConnectionError:
        print(f"[DingTalk] 推送中止，无法获取 Access Token。")
        return

    count = len(new_notifications)
    print(f"[DingTalk] 准备推送 Channel: {channel_name} ({count} 条新通知)...")

    # 🚨 构造单条汇总 Markdown 消息
    message_markdown_text = format_channel_update_markdown(
        channel_name, 
        site_name, 
        new_notifications
    )
    
    # 构造 msgParam (Markdown 模板结构)
    msg_param_data = {
        # 消息卡片标题应简洁地概括更新内容
        "title": f"【{site_name}】{channel_name} 发现 {count} 条新通知",
        "text": message_markdown_text
    }
    msg_param_json = json.dumps(msg_param_data)
    
    # 构造请求头
    org_group_send_headers = dingtalk_robot_models.OrgGroupSendHeaders()
    org_group_send_headers.x_acs_dingtalk_access_token = access_token
    
    # 构造请求体
    org_group_send_request = dingtalk_robot_models.OrgGroupSendRequest(
        msg_param=msg_param_json,
        msg_key='sampleMarkdown',
        open_conversation_id=DINGTALK_CONVERSATION_ID,
        robot_code=DINGTALK_ROBOT_CODE
    )

    try:
        DINGTALK_ROBOT_CLIENT.org_group_send_with_options(
            org_group_send_request, 
            org_group_send_headers, 
            util_models.RuntimeOptions(read_timeout=3000, connect_timeout=3000)
        )
        print(f"[DingTalk] 成功推送 Channel: {channel_name} ({count} 条新通知)")
        
    except Exception as err:
        print(f"[DingTalk ERROR] 推送失败: Channel {channel_name}")
        if hasattr(err, 'code') and hasattr(err, 'message'):
            print(f"Error Type: SDK Error, Code: {err.code}, Message: {err.message}")
        else:
            print(f"Error Type: Python Error, Details: {type(err).__name__}: {err}")