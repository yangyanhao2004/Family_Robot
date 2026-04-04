from typing import Dict, Any
from models.status import StatusMessage
from models.webrtc import WebRTCSignalingMessage
from core.connection_manager import manager
from models.common import ErrorMessage

async def handle_status_message(message: Dict[str, Any]):
    try:
        status_msg = StatusMessage(**message)
    except Exception as e:
        error_msg = ErrorMessage(
            type="error",
            message=f"消息格式非法: {str(e)}"
        )
        await manager.send_to_pi(error_msg.model_dump())

async def handle_webrtc_signaling_message(message: Dict[str, Any]):
    try:
        signaling_msg = WebRTCSignalingMessage(**message)
    except Exception as e:
        error_msg = ErrorMessage(
            type="error",
            message=f"消息格式非法: {str(e)}"
        )
        await manager.send_to_pi(error_msg.model_dump())
