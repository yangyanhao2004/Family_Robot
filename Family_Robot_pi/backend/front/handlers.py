from typing import Dict, Any
from backend.models.command import CommandMessage
from backend.models.webrtc import WebRTCSignalingMessage
from backend.core.connection_manager import manager
from backend.models.common import ErrorMessage

async def handle_command_message(message: Dict[str, Any]):
    try:
        CommandMessage(**message)
        if not manager.is_pi_connected():
            await manager.send_to_web(ErrorMessage(
                type="error", message="Robot not connected"
            ).model_dump())
    except Exception as e:
        await manager.send_to_web(ErrorMessage(
            type="error", message=f"Invalid message format: {e}"
        ).model_dump())

async def handle_webrtc_signaling_message(message: Dict[str, Any]):
    try:
        WebRTCSignalingMessage(**message)
    except Exception as e:
        await manager.send_to_web(ErrorMessage(
            type="error", message=f"Invalid message format: {e}"
        ).model_dump())
