from typing import Dict, Any
from models.command import CommandMessage
from models.webrtc import WebRTCSignalingMessage
from core.connection_manager import manager
from models.common import ErrorMessage

async def handle_command_message(message: Dict[str, Any]):
    try:
        command_msg = CommandMessage(**message)
        if not manager.is_pi_connected():
            error_msg = ErrorMessage(
                type="error",
                message="机器人未连接"
            )
            await manager.send_to_web(error_msg.model_dump())
    except Exception as e:
        error_msg = ErrorMessage(
            type="error",
            message=f"消息格式非法: {str(e)}"
        )
        await manager.send_to_web(error_msg.model_dump())

async def handle_webrtc_signaling_message(message: Dict[str, Any]):
    try:
        signaling_msg = WebRTCSignalingMessage(**message)
    except Exception as e:
        error_msg = ErrorMessage(
            type="error",
            message=f"消息格式非法: {str(e)}"
        )
        await manager.send_to_web(error_msg.model_dump())
