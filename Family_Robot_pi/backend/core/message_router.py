import logging
from typing import Dict, Any
from backend.core.connection_manager import manager

logger = logging.getLogger('backend.router')

class MessageRouter:
    async def route_message(self, sender_role: str, message: Dict[str, Any]):
        message_type = message.get("type")

        if sender_role == "web":
            if message_type == "command":
                await manager.send_to_pi(message)
            elif message_type == "webrtc_signaling":
                await manager.send_to_pi(message)
            else:
                logger.warning(f"Unknown web message type: {message_type}")

        elif sender_role == "robot":
            if message_type == "status":
                await manager.send_to_web(message)
            elif message_type == "webrtc_signaling":
                await manager.send_to_web(message)
            else:
                logger.warning(f"Unknown Pi message type: {message_type}")

router = MessageRouter()
