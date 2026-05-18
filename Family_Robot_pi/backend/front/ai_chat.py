"""
WebSocket handler for ai_chat messages.

Handles the full lifecycle: receive -> route to Kimi K2.5 -> execute tool -> respond.
"""

import json
import logging
import os
from typing import Dict, Any, Optional

import httpx

from backend.core.connection_manager import manager
from brain.web_ai_client import KimiK25Client, WEB_AI_TOOLS, get_web_ai_system_prompt
from brain.session_manager import session_manager

logger = logging.getLogger("backend.front.ai_chat")

_kimi_client: Optional[KimiK25Client] = None

VALID_COMMANDS = {"forward", "backward", "left", "right", "stop", "servo1", "servo2"}


def _get_kimi() -> KimiK25Client:
    global _kimi_client
    if _kimi_client is None:
        _kimi_client = KimiK25Client()
    return _kimi_client


async def handle_ai_chat(message: Dict[str, Any]):
    payload = message.get("payload", {})
    user_id = payload.get("user_id")
    user_text = payload.get("message", "").strip()

    if not user_id or not user_text:
        await manager.send_to_web({
            "type": "ai_chat_response",
            "payload": {"text": "Please provide a valid message.", "action": "chat_reply"}
        })
        return

    session = session_manager.get_or_create(int(user_id))
    session.add_message("user", user_text)

    api_messages = [{"role": "system", "content": get_web_ai_system_prompt()}]
    api_messages.extend(session.get_messages())

    try:
        kimi = _get_kimi()
        response = await kimi.chat(api_messages, tools=WEB_AI_TOOLS)

        if response.is_tool_call:
            for tc in response.tool_calls:
                await _execute_tool_call(tc, session, int(user_id))
        else:
            reply_text = response.content or "Sorry, I didn't understand."
            session.add_message("assistant", reply_text)
            await manager.send_to_web({
                "type": "ai_chat_response",
                "payload": {"text": reply_text, "action": "chat_reply"}
            })
    except Exception as e:
        logger.error("AI chat error: %s", e)
        if "401" in str(e) or "Unauthorized" in str(e):
            _kimi_client = None
        await manager.send_to_web({
            "type": "ai_chat_response",
            "payload": {"text": "Sorry, I encountered an error. Please try again.", "action": "chat_reply"}
        })


async def _execute_tool_call(tc, session, user_id: int):
    name = tc.name
    args = tc.arguments

    if name == "chat_reply":
        text = args.get("reply", "")
        session.add_message("assistant", text)
        await manager.send_to_web({
            "type": "ai_chat_response",
            "payload": {"text": text, "action": "chat_reply"}
        })

    elif name == "control_robot":
        command = args.get("command", "stop")
        angle = args.get("angle", 90)
        explanation = args.get("explanation", f"Executing {command}")

        if command not in VALID_COMMANDS:
            command = "stop"

        await manager.send_to_pi({
            "type": "command",
            "payload": {"command": command, "angle": angle}
        })

        session.add_message("assistant", explanation)
        await manager.send_to_web({
            "type": "ai_chat_response",
            "payload": {
                "text": explanation,
                "action": "control_robot",
                "data": {"command": command, "angle": angle}
            }
        })

    elif name == "set_reminder":
        reminder_text = args.get("reminder", "")
        scheduled_time = args.get("scheduled_time", "")
        method = args.get("method", "EMAIL")
        email = args.get("email", "")

        success = await _store_reminder_in_java(user_id, reminder_text, scheduled_time, method, email)

        reply = (f"Reminder set: '{reminder_text}' ({method})" if success
                 else "Failed to set reminder. Please try again.")
        session.add_message("assistant", reply)
        await manager.send_to_web({
            "type": "ai_chat_response",
            "payload": {"text": reply, "action": "set_reminder"}
        })


async def _store_reminder_in_java(
    user_id: int, text: str, scheduled_time: str, method: str, email: str
) -> bool:
    java_url = os.getenv("JAVA_BACKEND_URL", "http://localhost:8090")
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(
                f"{java_url}/api/reminders",
                json={
                    "userId": user_id,
                    "text": text,
                    "scheduledTime": scheduled_time,
                    "method": method,
                    "email": email,
                }
            )
            return resp.status_code == 201
    except Exception as e:
        logger.error("Failed to store reminder: %s", e)
        return False


async def handle_ai_session_end(user_id: int):
    session_manager.destroy(user_id)


async def cleanup_session_for_disconnect(websocket_id: int, user_id_map: Dict[int, int]):
    user_id = user_id_map.pop(websocket_id, None)
    if user_id is not None:
        session_manager.destroy(user_id)
    return user_id
