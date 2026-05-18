"""
Kimi K2.5 async client for Web AI Chat with function calling.
"""

import json
import os
from typing import Optional, List, Dict, Any
from dataclasses import dataclass

import httpx

# ---- Tool Definitions ----

WEB_AI_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "chat_reply",
            "description": "Send a text reply to the user. Use this when the user wants to chat, ask questions, or have a conversation. Also use this to ask clarifying questions when the user's request is ambiguous.",
            "parameters": {
                "type": "object",
                "properties": {
                    "reply": {
                        "type": "string",
                        "description": "The text reply to send to the user. Be friendly, concise, and helpful."
                    }
                },
                "required": ["reply"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "control_robot",
            "description": "Control the physical robot. Use this when the user asks the robot to move (forward, backward, left, right, stop) or adjust its servo/camera angles (servo1 for horizontal pan, servo2 for vertical tilt).",
            "parameters": {
                "type": "object",
                "properties": {
                    "command": {
                        "type": "string",
                        "enum": ["forward", "backward", "left", "right", "stop", "servo1", "servo2"],
                        "description": "The robot command: forward/backward/left/right for movement, stop to halt, servo1 for horizontal pan (0-180 degrees), servo2 for vertical tilt (0-180 degrees)."
                    },
                    "angle": {
                        "type": "number",
                        "description": "Angle for servo commands (0-180). Default 90 is centered."
                    },
                    "explanation": {
                        "type": "string",
                        "description": "A brief, friendly explanation to tell the user what the robot is doing, in the user's language."
                    }
                },
                "required": ["command", "explanation"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "set_reminder",
            "description": "Create a reminder. Use EMAIL method when the user asks to be reminded via email. Use VOICE method when the user asks to be reminded via the robot's speaker/voice announcement.",
            "parameters": {
                "type": "object",
                "properties": {
                    "reminder": {
                        "type": "string",
                        "description": "The reminder content/message."
                    },
                    "scheduled_time": {
                        "type": "string",
                        "description": "ISO 8601 datetime string in Asia/Shanghai timezone, e.g. '2026-05-19T14:30:00'."
                    },
                    "method": {
                        "type": "string",
                        "enum": ["EMAIL", "VOICE"],
                        "description": "EMAIL for email reminders, VOICE for speaker voice reminders."
                    },
                    "email": {
                        "type": "string",
                        "description": "The user's email address. Required when method is EMAIL."
                    }
                },
                "required": ["reminder", "scheduled_time", "method"]
            }
        }
    }
]

WEB_AI_SYSTEM_PROMPT = """You are Jarvis, a helpful home robot assistant. You can:

1. Chat with users naturally (use chat_reply)
2. Control a physical robot with movement and camera servos (use control_robot)
3. Set reminders for the user — via email or voice speaker (use set_reminder)

IMPORTANT RULES:
- Always use the tools provided. Do NOT respond with plain text when a tool is appropriate.
- When asked to move the robot, use control_robot with the correct command and a friendly explanation.
- When asked to set a reminder, extract: what to remind about, when (as ISO 8601 in Asia/Shanghai timezone), method (EMAIL or VOICE), and the user's email if needed.
- For servo commands: servo1 = horizontal pan, servo2 = vertical tilt. Angle 90 is center.
- Keep responses concise and friendly. Use the same language as the user.
- If the user says something ambiguous, ask clarifying questions via chat_reply.
- Use only ONE tool per response. Do not combine multiple tools in one call."""


@dataclass
class ToolCall:
    name: str
    arguments: Dict[str, Any]


@dataclass
class ChatResponse:
    content: Optional[str] = None
    tool_calls: List[ToolCall] = None  # type: ignore[assignment]
    is_tool_call: bool = False

    def __post_init__(self):
        if self.tool_calls is None:
            self.tool_calls = []


class KimiK25Client:
    """Async client for Kimi K2.5 (Moonshot API) with function calling."""

    BASE_URL = "https://api.moonshot.cn/v1"
    MODEL = "kimi-k2.5"

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("MOONSHOT_API_KEY")
        if not self.api_key:
            raise ValueError("Moonshot API key required")

        self.client = httpx.AsyncClient(
            timeout=120.0,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
        )

    async def chat(
        self,
        messages: List[Dict[str, str]],
        tools: Optional[List[Dict]] = None,
    ) -> ChatResponse:
        """Send multi-turn messages to Kimi K2.5 with optional tools."""
        payload: Dict[str, Any] = {
            "model": self.MODEL,
            "messages": messages,
            "stream": False,
            "temperature": 1.0,
        }

        if tools:
            payload["tools"] = tools
            payload["tool_choice"] = "auto"

        response = await self.client.post(
            f"{self.BASE_URL}/chat/completions",
            json=payload
        )
        response.raise_for_status()
        body = response.json()

        choice = body["choices"][0]
        message = choice["message"]

        tool_calls = []
        if message.get("tool_calls"):
            for tc in message["tool_calls"]:
                func = tc["function"]
                try:
                    args = json.loads(func["arguments"])
                except (json.JSONDecodeError, KeyError):
                    args = {}
                tool_calls.append(ToolCall(name=func["name"], arguments=args))
            return ChatResponse(
                content=message.get("content"),
                tool_calls=tool_calls,
                is_tool_call=True
            )

        return ChatResponse(
            content=message.get("content", ""),
            is_tool_call=False
        )

    async def close(self):
        await self.client.aclose()
