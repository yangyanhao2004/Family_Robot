"""Internal endpoint for receiving voice reminders from Java backend."""

import logging
import re

from fastapi import APIRouter
from pydantic import BaseModel

from backend.core.connection_manager import manager
from brain.web_ai_client import KimiK25Client

logger = logging.getLogger("backend.internal.voice_reminder")

router = APIRouter(prefix="/internal", tags=["internal"])

_CHINESE_PATTERN = re.compile(r'[一-鿿]')


class VoiceReminderRequest(BaseModel):
    reminderId: int
    text: str
    userId: int


async def _translate_to_english(text: str) -> str:
    """Translate Chinese text to English via Kimi API for TTS compatibility."""
    try:
        client = KimiK25Client()
        messages = [
            {"role": "system", "content": "You are a translator. Translate the following Chinese text to English. Output ONLY the English translation, nothing else. Keep it concise and natural."},
            {"role": "user", "content": text},
        ]
        response = await client.chat(messages)
        await client.close()
        translated = (response.content or text).strip()
        logger.info("Translated reminder text: '%s' -> '%s'", text, translated)
        return translated
    except Exception as e:
        logger.error("Translation failed for reminder text: %s", e)
        return text


@router.post("/voice-reminder")
async def handle_voice_reminder(req: VoiceReminderRequest):
    logger.info("Voice reminder #%d for user %d: %s", req.reminderId, req.userId, req.text)

    text = req.text
    if _CHINESE_PATTERN.search(text):
        text = await _translate_to_english(text)

    await manager.send_to_pi({
        "type": "voice_reminder",
        "payload": {"text": text, "reminder_id": req.reminderId}
    })
    return {"status": "sent", "reminderId": req.reminderId}
