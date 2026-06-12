"""
Emergency fall detection HTTP endpoint.
"""

import asyncio
import logging
from typing import Optional, Callable

import httpx
from fastapi import APIRouter
from pydantic import BaseModel

from backend.core.connection_manager import manager

logger = logging.getLogger("backend.emergency")

router = APIRouter(prefix="/emergency", tags=["emergency"])

# Injected by main.py at startup so the alert can trigger local TTS
alert_callback: Optional[Callable[[str], None]] = None


def set_alert_callback(cb: Callable[[str], None]):
    """Register a callback that plays an alert via the orchestrator's TTS."""
    global alert_callback
    alert_callback = cb


class FallAlertRequest(BaseModel):
    userId: int
    userName: str = "用户"


@router.post("/fall")
async def handle_fall_alert(req: FallAlertRequest):
    """Receive a fall event and execute the full alert pipeline."""
    user_id = req.userId
    user_name = req.userName or "用户"
    java_url = __import__("os").getenv("JAVA_BACKEND_URL", "http://localhost:8090")

    logger.info("Fall alert triggered for user %d (%s)", user_id, user_name)

    # 1. Ask Java to send emergency email (fire-and-forget)
    mail_result = "email_skipped"
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(
                f"{java_url}/api/emergency/send-mail",
                json={"userId": user_id},
            )
            if resp.status_code == 200:
                data = resp.json()
                mail_result = data.get("contactEmail", "sent")
                logger.info("Emergency mail sent to %s", mail_result)
            else:
                mail_result = f"email_failed_{resp.status_code}"
                logger.warning("Emergency mail failed: %s", resp.text)
    except Exception as e:
        mail_result = f"email_error: {e}"
        logger.error("Emergency mail error: %s", e)

    # 2. TTS local alert via the orchestrator
    try:
        if alert_callback:
            alert_msg = f"检测到{user_name}可能摔倒！已通知紧急联系人，请尽快确认安全。"
            alert_callback(alert_msg)
            logger.info("TTS alert triggered")
        else:
            logger.warning("No alert_callback registered — TTS skipped")
    except Exception as e:
        logger.error("TTS alert error: %s", e)

    # 3. Push alert to all connected web clients
    try:
        await manager.send_to_web({
            "type": "fall_alert",
            "payload": {
                "userId": user_id,
                "userName": user_name,
                "message": f"检测到{user_name}可能摔倒！",
                "contactEmail": mail_result if "@" in str(mail_result) else "",
            },
        })
    except Exception as e:
        logger.error("WebSocket push error: %s", e)

    return {
        "status": "ok",
        "mailResult": mail_result,
        "ttsTriggered": alert_callback is not None,
    }
