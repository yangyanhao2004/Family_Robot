import os
import time
from datetime import datetime, timezone, timedelta
from typing import Dict, Any
from backend.models.command import CommandMessage
from backend.models.webrtc import WebRTCSignalingMessage
from backend.core.connection_manager import manager
from backend.core.video_stream import video_hub
from backend.models.common import ErrorMessage

PHOTOS_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "photos")
PHOTO_BASE_URL = "/photos"

tz = timezone(timedelta(hours=8))

async def handle_command_message(message: Dict[str, Any]) -> bool:
    """Returns True if the command should be forwarded to Pi."""
    try:
        cmd = CommandMessage(**message)
        cmd_str = cmd.payload.command

        if cmd_str == "take_photo":
            await _handle_take_photo()
            return False  # handled locally, don't forward to Pi

        # Movement/light commands need Pi
        if not manager.is_pi_connected():
            await manager.send_to_web(ErrorMessage(
                type="error", message="Robot not connected"
            ).model_dump())
            return False
        return True
    except Exception as e:
        await manager.send_to_web(ErrorMessage(
            type="error", message=f"Invalid message format: {e}"
        ).model_dump())
        return False


async def _handle_take_photo():
    frame_bytes = video_hub.latest_frame
    if not frame_bytes:
        await manager.send_to_web(ErrorMessage(
            type="error", message="No camera frame available yet"
        ).model_dump())
        return

    os.makedirs(PHOTOS_DIR, exist_ok=True)

    ts = datetime.now(tz).strftime("%Y%m%d_%H%M%S")
    filename = f"photo_{ts}.jpg"
    filepath = os.path.join(PHOTOS_DIR, filename)

    with open(filepath, "wb") as f:
        f.write(frame_bytes)

    url = f"{PHOTO_BASE_URL}/{filename}"

    await manager.send_to_web({
        "type": "photo_captured",
        "payload": {
            "url": url,
            "filename": filename,
            "date": datetime.now(tz).strftime("%Y-%m-%d"),
        },
    })


async def handle_webrtc_signaling_message(message: Dict[str, Any]):
    try:
        WebRTCSignalingMessage(**message)
    except Exception as e:
        await manager.send_to_web(ErrorMessage(
            type="error", message=f"Invalid message format: {e}"
        ).model_dump())
