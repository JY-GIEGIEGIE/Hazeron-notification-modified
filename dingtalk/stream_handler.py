# dingtalk/stream_handler.py

import dingtalk_stream
import logging
from typing import Callable, Any, Dict, Awaitable

# --- 1. 业务逻辑处理的抽象接口 ---
# MessageHandler: 外部传入的业务处理函数类型别名。
# 签名要求：必须是异步函数 (Awaitable)，接收一个消息字典 (Dict[str, Any])，并返回一个字符串回复 (str)。
MessageHandler = Callable[[Dict[str, Any]], Awaitable[str]]


class CustomChatbotHandler(dingtalk_stream.ChatbotHandler):
    """
    继承自 SDK 的 ChatbotHandler，负责接收、解包钉钉 Stream 消息，
    并转发给外部业务逻辑函数 (business_handler)。
    """
    def __init__(self, logger: logging.Logger, business_handler: MessageHandler):
        # 继承自 dingtalk_stream.ChatbotHandler
        super().__init__() 
        self.logger = logger
        self.business_handler = business_handler
        self.logger.info("CustomChatbotHandler initialized with external business logic.")

    async def process(self, callback: dingtalk_stream.CallbackMessage):
        """
        钉钉 Stream SDK 调用的核心方法。
        """
        try:
            # 1. 解析消息：将原始回调数据解析为 ChatbotMessage
            incoming_message = dingtalk_stream.ChatbotMessage.from_dict(callback.data)
            
            # 2. 提取并标准化消息字典
            message_dict = {
                "text": incoming_message.text.content.strip(),
                "sender_nick": incoming_message.sender_nick,
                "conversation_id": incoming_message.conversation_id,
                # 提取其他关键字段，供业务逻辑使用
                "sender_corp_id": incoming_message.sender_corp_id,
                "sender_staff_id": incoming_message.sender_staff_id,
            }

            self.logger.info(f"Received message from {message_dict['sender_nick']}: {message_dict['text']}")
            
            # 3. **调用外部业务逻辑**：等待异步业务函数返回回复文本
            response_text = await self.business_handler(message_dict)

            # 4. 更新：使用markdown回复
            markdown_title = "Hazeron"
            self.reply_markdown(markdown_title, response_text, incoming_message) 

            # 5. 返回确认状态：表示消息处理成功
            return dingtalk_stream.AckMessage.STATUS_OK, 'OK'

        except Exception as e:
            self.logger.error(f"Error processing DingTalk message: {e}", exc_info=True)
            # 即使失败，最好返回 OK 让钉钉停止重试
            return dingtalk_stream.AckMessage.STATUS_OK, f'Error: {e}'


class DingTalkStreamProcessor:
    """
    封装了钉钉 Stream 客户端的初始化和运行逻辑。
    """
    def __init__(self, client_id: str, client_secret: str, logger: logging.Logger):
        self.client_id = client_id
        self.client_secret = client_secret
        self.logger = logger
        self.client = None
        self.logger.info("DingTalkStreamProcessor initialized.")

    def register_business_handler(self, handler_function: MessageHandler):
        """
        注册外部业务处理函数，并初始化 SDK 客户端。
        :param handler_function: 外部的异步业务逻辑函数 (来自 message_handler.py)。
        """
        # 1. 初始化 SDK 客户端
        credential = dingtalk_stream.Credential(self.client_id, self.client_secret)
        # 将 logger 注入到 SDK 客户端
        self.client = dingtalk_stream.DingTalkStreamClient(credential, logger=self.logger)
        
        # 2. 注册自定义回调处理器
        handler = CustomChatbotHandler(self.logger, handler_function)
        self.client.register_callback_handler(dingtalk_stream.chatbot.ChatbotMessage.TOPIC, handler)
        
        self.logger.info("DingTalk client and custom handler registered.")

    def start_running(self):
        """
        启动 Stream 客户端的长连接。这是一个阻塞调用。
        """
        if not self.client:
            raise RuntimeError("Client not registered. Call register_business_handler first.")
        
        # 使用 start_forever 启动长连接
        self.client.start_forever()


def start_dingtalk_client(client_id: str, client_secret: str, logger: logging.Logger, message_handler_func: MessageHandler):
    """
    提供给主应用调用的启动接口。封装了初始化、注册和启动的整个流程。
    
    :param client_id: 钉钉应用 AppKey。
    :param client_secret: 钉钉应用 AppSecret。
    :param logger: 项目的 logging 实例。
    :param message_handler_func: 外部处理用户消息的异步函数（即 handle_user_command）。
    """
    processor = DingTalkStreamProcessor(client_id, client_secret, logger)
    processor.register_business_handler(message_handler_func) 
    
    logger.info("钉钉客户端配置完成，正在启动长连接...")
    processor.start_running()