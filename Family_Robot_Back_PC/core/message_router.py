import logging
from typing import Optional, Dict, Any, Callable
from .connection_manager import manager

# 配置日志
logger = logging.getLogger('backend.router')

class MessageRouter:
    def __init__(self):
        self.web_handlers: Dict[str, Callable] = {}
        self.pi_handlers: Dict[str, Callable] = {}

    def register_web_handler(self, message_type: str, handler: Callable):
        logger.info(f"注册前端消息处理器: {message_type}")
        self.web_handlers[message_type] = handler

    def register_pi_handler(self, message_type: str, handler: Callable):
        logger.info(f"注册树莓派消息处理器: {message_type}")
        self.pi_handlers[message_type] = handler

    async def route_message(self, sender_role: str, message: Dict[str, Any]):
        message_type = message.get("type")
        logger.debug(f"路由消息 - 发送者: {sender_role}, 消息类型: {message_type}, 消息内容: {message}")
        
        if sender_role == "web":
            if message_type == "command":
                logger.info(f"将前端控制指令路由到树莓派: {message.get('payload', {}).get('command')}")
                await manager.send_to_pi(message)
            elif message_type == "webrtc_signaling":
                logger.info("将前端 WebRTC 信令路由到树莓派")
                await manager.send_to_pi(message)
            elif message_type in self.web_handlers:
                logger.info(f"使用前端处理器处理消息类型: {message_type}")
                await self.web_handlers[message_type](message)
            else:
                logger.warning(f"未知的前端消息类型: {message_type}")
        
        elif sender_role == "robot":
            if message_type == "status":
                logger.info("将树莓派状态消息路由到前端")
                await manager.send_to_web(message)
            elif message_type == "webrtc_signaling":
                logger.info("将树莓派 WebRTC 信令路由到前端")
                await manager.send_to_web(message)
            elif message_type in self.pi_handlers:
                logger.info(f"使用树莓派处理器处理消息类型: {message_type}")
                await self.pi_handlers[message_type](message)
            else:
                logger.warning(f"未知的树莓派消息类型: {message_type}")

router = MessageRouter()
