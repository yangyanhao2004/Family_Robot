"""Internal endpoint for receiving voice reminders from Java backend."""

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


@router.post("/voice-reminder")
async def handle_voice_reminder(req: VoiceReminderRequest):
    logger.info("Voice reminder #%d for user %d: %s", req.reminderId, req.userId, req.text)
    await manager.send_to_pi({
        "type": "voice_reminder",
        "payload": {"text": req.text, "reminder_id": req.reminderId}
    })
    return {"status": "sent", "reminderId": req.reminderId}
