from typing import Dict, Any
from backend.models.status import StatusMessage
from backend.models.webrtc import WebRTCSignalingMessage
from backend.core.connection_manager import manager
from backend.models.common import ErrorMessage

async def handle_status_message(message: Dict[str, Any]):
    try:
        StatusMessage(**message)
    except Exception as e:
        await manager.send_to_pi(ErrorMessage(
            type="error", message=f"Invalid message format: {e}"
        ).model_dump())

async def handle_webrtc_signaling_message(message: Dict[str, Any]):
    try:
        WebRTCSignalingMessage(**message)
    except Exception as e:
        await manager.send_to_pi(ErrorMessage(
            type="error", message=f"Invalid message format: {e}"
        ).model_dump())
