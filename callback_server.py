# callback_server.py
import logging

from dingtalk.stream_handler import start_dingtalk_client
from dingtalk.message_handler import handle_user_command

from config.secret_config import CLIENT_ID, CLIENT_SECRET


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

def start_callback_server():
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