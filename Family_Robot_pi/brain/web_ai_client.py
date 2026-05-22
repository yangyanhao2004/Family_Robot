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
            "description": "Control the physical robot. Use this when the user asks the robot to move (forward, backward, left, right, stop) or adjust its servo/camera angles (servo1 for horizontal pan, servo2 for vertical tilt). ALWAYS use this tool for stop/halt commands — never use chat_reply for stopping the robot.",
            "parameters": {
                "type": "object",
                "properties": {
                    "command": {
                        "type": "string",
                        "enum": ["forward", "backward", "left", "right", "stop", "servo1", "servo2"],
                        "description": "The robot command: forward/backward/left/right for movement, stop to halt, servo1 for horizontal pan (0-180 degrees), servo2 for vertical tilt (0-180 degrees). IMPORTANT: when the user says stop/halt/停/停下, you MUST use command='stop' with this tool."
                    },
                    "angle": {
                        "type": "number",
                        "description": "Angle for servo commands (0-180). Default 90 is centered."
                    },
                    "duration": {
                        "type": "number",
                        "description": "Duration in seconds for movement commands (forward/backward/left/right only). Convert degrees to seconds for turns: ~25°/second. Always use this when the user specifies a time or angle."
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
            "description": "Create a reminder. Use EMAIL method when the user asks to be reminded via email. Use VOICE method when the user asks to be reminded via the robot's speaker/voice/语音 announcement. IMPORTANT: only call this when the user has clearly specified the method (EMAIL or VOICE).",
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

import datetime


def get_web_ai_system_prompt() -> str:
    tz = datetime.timezone(datetime.timedelta(hours=8))
    now = datetime.datetime.now(tz).strftime("%Y-%m-%dT%H:%M:%S")
    return f"""You are Jarvis, a helpful home robot assistant. You can:

1. Chat with users naturally (use chat_reply)
2. Control a physical robot with movement and camera servos (use control_robot)
3. Set reminders for the user — via email or voice speaker (use set_reminder)

The current time is {now} (Asia/Shanghai timezone, UTC+8).
When the user says a relative time like "1 minute later" or "in 5 minutes" or "tomorrow at 3pm",
calculate the absolute ISO 8601 datetime yourself using this current time.

CRITICAL RULES — YOU MUST FOLLOW THESE EXACTLY:
- When the user asks the robot to move (forward/backward/left/right) — including Chinese phrases like 前进/后退/左转/右转/往前/往后/向前/向后/往前走/往前跑/向前移动/去前面 — you MUST call control_robot. NEVER use chat_reply for movement requests. The robot will NOT move if you just reply with text.
- When the user says "stop", "halt", "停下", "停", or any variation of stopping the robot, you MUST use control_robot with command="stop". Never use chat_reply for this — the robot will NOT actually stop unless you call control_robot.
- When asked to move the robot for a specific duration (e.g. "forward for 2 seconds", "前进2秒", "往前走5秒"), use control_robot with the duration parameter set to that number of seconds. The robot will stop automatically after that time.
- When asked to move the robot without a duration (e.g. "go forward", "前进"), do NOT include the duration parameter — the robot will keep moving until told to stop.
- The robot CANNOT turn to a precise angle in degrees (it has no gyroscope or angle sensor). Turning is controlled by duration in seconds. When the user specifies a turn angle like "左转45度" or "turn right 90 degrees", convert the angle to duration using this approximate ratio: the robot turns roughly 25 degrees per second at default speed. So: 25° ≈ 1 second, 45° ≈ 2 seconds, 90° ≈ 4 seconds. Set the duration parameter accordingly and mention in the explanation: "Turning left for X seconds, about Y degrees." This makes it clear to the user that the turn is time-based and approximate.
- When asked to adjust the servo/camera (including phrases like 转动舵机/看左边/看右边/抬头/低头/云台), use control_robot with the servo1 or servo2 command.
- When asked to set a reminder, extract: what to remind about, when (as ISO 8601 in Asia/Shanghai timezone), method (EMAIL or VOICE), and the user's email if needed. Always calculate the absolute time yourself — NEVER ask the user what time it is now.
- CRITICAL: If the user asks to set a reminder but does NOT specify the method (EMAIL or VOICE), do NOT call set_reminder. Instead, use chat_reply to ask: 'How would you like to be reminded — by voice announcement on the robot speaker, or by email?' Only call set_reminder after the user responds with a clear method choice.
- For servo commands: servo1 = horizontal pan (0=far right, 180=far left, 90=center). servo2 = vertical tilt (0=tilt all the way UP, 180=tilt all the way DOWN, 90=center/level). So "look left" means servo1 angle > 90, "look right" means servo1 angle < 90. "tilt up 30 degrees" means servo2 angle=60, "tilt down 20 degrees" means servo2 angle=110.
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
        tool_choice: Optional[str] = None,
    ) -> ChatResponse:
        """Send multi-turn messages to Kimi K2.5 with optional tools.

        Args:
            tool_choice: Force a specific function name, or None for auto.
        """
        payload: Dict[str, Any] = {
            "model": self.MODEL,
            "messages": messages,
            "stream": False,
            "temperature": 1.0,
        }

        if tools:
            payload["tools"] = tools
            if tool_choice:
                payload["tool_choice"] = {"type": "function", "function": {"name": tool_choice}}
            else:
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
