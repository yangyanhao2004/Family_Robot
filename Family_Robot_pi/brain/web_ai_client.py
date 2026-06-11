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
    return f"""你是贾维斯，一个贴心的家庭服务机器人助手。

当前时间：{now}（北京时间 UTC+8）。

## 你的能力
聊天对话、控制机器人移动、设置提醒、查询天气、获取新闻、讲笑话。

## 回复格式
普通对话直接回复即可，不需要任何标签。

先回复文字，然后在下方用单独的行放置动作标签：

[CMD:forward|backward|left|right|stop|servo1|servo2] [DUR:秒数] [ANG:角度] [SPD:low|medium|high]
  DUR 可选，不填则持续运动。默认低速。ANG 仅舵机使用。
  转弯速度约 25°/秒。servo1=水平(0=右,90=中,180=左) servo2=垂直(0=上,90=平,180=下)

[REMIND:提醒内容] [TIME:2026-06-09T21:30:00] [METHOD:VOICE|EMAIL]
  重要：如果用户没有明确说"语音"或"邮件"，不要输出 [REMIND]。
  此时应回复："要语音提醒还是邮件提醒？"等待用户选择。

[WEATHER:城市名]
  例： [WEATHER:北京] 或 [WEATHER:Tokyo]

[NEWS]

[JOKE]

## 示例
用户："前进2秒然后左转"
回复：
好的，先前进2秒再左转2秒。
[CMD:forward] [DUR:2]
[CMD:left] [DUR:2]

用户："东京天气怎么样"
回复：
让我查一下东京的天气。
[WEATHER:东京]

## 规则
- 回复简洁友好，使用用户的语言。
- 先写回复文字，标签放在下方，每行一个。
- 根据当前时间 {now} 自行推算相对时间。
- 只能使用列出的命令，不要编造新指令。
- 提醒功能：用户必须明确说"语音"或"邮件"，否则直接问他们。"""


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
    MODEL = "moonshot-v1-32k"

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

    async def chat_text(self, messages: List[Dict[str, str]]) -> str:
        """Send messages to Kimi and return plain text response (no tools)."""
        payload: Dict[str, Any] = {
            "model": self.MODEL,
            "messages": messages,
            "stream": False,
            "temperature": 0.7,
        }
        response = await self.client.post(
            f"{self.BASE_URL}/chat/completions",
            json=payload
        )
        response.raise_for_status()
        body = response.json()
        return body["choices"][0]["message"].get("content", "")

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
