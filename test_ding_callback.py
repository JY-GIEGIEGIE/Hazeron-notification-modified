# main.py

import logging
import json
import os
from typing import Dict, Any

# 导入我们封装好的核心函数
from dingtalk.stream_handler import start_dingtalk_client
from dingtalk.message_handler import handle_user_command

# --------------------------------------------------
# 1. 启动配置
# --------------------------------------------------
# 🚨 请在这里替换您的真实配置

CONFIG_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    'config', 
    'secret_config.json'
)

CLIENT_ID = None
CLIENT_SECRET = None

try:
    if not os.path.exists(CONFIG_PATH):
        raise FileNotFoundError(f"配置文件未找到：{CONFIG_PATH}")
        
    with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
        config_data = json.load(f)
        
    # 从扁平结构中直接提取
    CLIENT_ID = config_data.get('CLIENT_ID')
    CLIENT_SECRET = config_data.get('CLIENT_SECRET')

except Exception as e:
    # 打印错误，但不中断程序，由后续的 None 检查处理
    print(f"🚨 严重错误：加载配置文件失败。请检查 config/secret_config.json 文件。\n详细信息: {e}")
    


def setup_logger():
    """设置应用级别的日志记录器。"""
    logger = logging.getLogger('DingBot')
    handler = logging.StreamHandler()
    formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(name)s: %(message)s')
    handler.setFormatter(formatter)
    
    if not logger.handlers:
        logger.addHandler(handler)
        
    logger.setLevel(logging.INFO)
    return logger

# --------------------------------------------------
# 2. 应用程序入口
# --------------------------------------------------

def run_application():
    """初始化配置、日志，并启动钉钉客户端。"""
    
    if "YOUR_CLIENT_ID" in CLIENT_ID:
        print("---------------------------------------------------------")
        print("🚨 错误：请在 main.py 文件中填入您的真实 CLIENT_ID 和 CLIENT_SECRET！")
        print("---------------------------------------------------------")
        return
        
    logger = setup_logger()
    logger.info("--- 正在启动 Hazeron DingTalk Stream 客户端 ---")

    try:
        # 调用封装好的函数：将 ID、Logger 和处理逻辑注入到客户端
        start_dingtalk_client(
            client_id=CLIENT_ID,
            client_secret=CLIENT_SECRET,
            logger=logger,
            message_handler_func=handle_user_command  # 调用 dingtalk/message_handler.py 中的函数
        )
    except KeyboardInterrupt:
        logger.info("程序被用户中断。")
    except Exception as e:
        logger.critical(f"应用启动失败: {e}", exc_info=True)

if __name__ == '__main__':
    run_application()