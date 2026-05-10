import logging
from typing import Dict, Any, Callable
from backend.core.connection_manager import manager

logger = logging.getLogger('backend.router')

class MessageRouter:
    def __init__(self):
        self.web_handlers: Dict[str, Callable] = {}
        self.pi_handlers: Dict[str, Callable] = {}

    def register_web_handler(self, message_type: str, handler: Callable):
        self.web_handlers[message_type] = handler

    def register_pi_handler(self, message_type: str, handler: Callable):
        self.pi_handlers[message_type] = handler

    async def route_message(self, sender_role: str, message: Dict[str, Any]):
        message_type = message.get("type")

        if sender_role == "web":
            if message_type == "command":
                await manager.send_to_pi(message)
            elif message_type == "webrtc_signaling":
                await manager.send_to_pi(message)
            elif message_type in self.web_handlers:
                await self.web_handlers[message_type](message)
            else:
                logger.warning(f"Unknown web message type: {message_type}")

        elif sender_role == "robot":
            if message_type == "status":
                await manager.send_to_web(message)
            elif message_type == "webrtc_signaling":
                await manager.send_to_web(message)
            elif message_type in self.pi_handlers:
                await self.pi_handlers[message_type](message)
            else:
                logger.warning(f"Unknown Pi message type: {message_type}")

router = MessageRouter()
