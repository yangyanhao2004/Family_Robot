"""Internal endpoint for receiving voice reminders from Java backend."""

import asyncio
import logging

from fastapi import APIRouter
from pydantic import BaseModel

from backend.core.connection_manager import manager

logger = logging.getLogger("backend.internal.voice_reminder")

router = APIRouter(prefix="/internal", tags=["internal"])


class VoiceReminderRequest(BaseModel):
    reminderId: int
    text: str
    userId: int


async def _process_voice_reminder(reminder_id: int, text: str, user_id: int):
    """Forward voice reminder to Pi in background."""
    try:
        await manager.send_to_pi({
            "type": "voice_reminder",
            "payload": {"text": text, "reminder_id": reminder_id}
        })
    except Exception as e:
        logger.error("Voice reminder #%d background processing failed: %s", reminder_id, e)


@router.post("/voice-reminder")
async def handle_voice_reminder(req: VoiceReminderRequest):
    logger.info("Voice reminder #%d for user %d: %s", req.reminderId, req.userId, req.text)

    # Return immediately so Java doesn't time out; process in background
    asyncio.create_task(_process_voice_reminder(req.reminderId, req.text, req.userId))

    return {"status": "accepted", "reminderId": req.reminderId}
