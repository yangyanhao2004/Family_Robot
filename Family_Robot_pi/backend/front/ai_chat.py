"""
WebSocket handler for ai_chat messages.

Handles the full lifecycle: receive -> route to Kimi K2.5 -> execute tool -> respond.
"""

import asyncio
import json
import logging
import os
import re
from typing import Dict, Any, Optional

import httpx

from backend.core.connection_manager import manager
from brain.web_ai_client import WEB_AI_TOOLS, get_web_ai_system_prompt
from brain.cloud_client import KimiClient
from brain.session_manager import session_manager
from brain.tools.weather_tool import WeatherTool
from brain.tools.news_tool import NewsTool
from brain.tools.joke_tool import get_joke

logger = logging.getLogger("backend.front.ai_chat")

_weather_tool: Optional[WeatherTool] = None
_news_tool: Optional[NewsTool] = None

def _get_weather() -> WeatherTool:
    global _weather_tool
    if _weather_tool is None:
        _weather_tool = WeatherTool()
    return _weather_tool

def _get_news() -> NewsTool:
    global _news_tool
    if _news_tool is None:
        _news_tool = NewsTool()
    return _news_tool

# Weather-related keywords for detection
_WEATHER_KW = re.compile(r'天气|weather|气温|温度|下雨|下雪|刮风|晴朗|几度|冷不冷|热不热|凉快|暖和')

# News-related keywords
_NEWS_KW = re.compile(r'新闻|news|头条|大事|发生什么|最新消息')

# Joke-related keywords
_JOKE_KW = re.compile(r'笑话|joke|讲个故事|段子|幽默|搞笑')

_kimi_client: Optional[KimiClient] = None
_chinese_pattern = re.compile(r'[一-鿿]')

VALID_COMMANDS = {"forward", "backward", "left", "right", "stop", "servo1", "servo2"}

# ---- Pre-filter: direct command interception (Scheme A) ----

_DIRECTION_MAP: Dict[str, str] = {
    '前进': 'forward', '往前': 'forward', '向前': 'forward', '往前走': 'forward',
    '往前跑': 'forward', '向前移动': 'forward', '去前面': 'forward', '向前走': 'forward',
    '后退': 'backward', '往后': 'backward', '向后': 'backward', '往后走': 'backward',
    '向后退': 'backward', '退后': 'backward',
    '左转': 'left', '往左': 'left', '向左': 'left', '左拐': 'left', '向左转': 'left',
    '右转': 'right', '往右': 'right', '向右': 'right', '右拐': 'right', '向右转': 'right',
}

_STOP_WORDS = {'停', '停下', '停止', '停下来', '停住', '站住', '别动'}

# Chinese numeral → digit mapping for prefilter
_CN_NUM_MAP = {
    '一': '1', '二': '2', '三': '3', '四': '4', '五': '5',
    '六': '6', '七': '7', '八': '8', '九': '9', '十': '10',
}

# Gaze/view phrases → servo commands (checked BEFORE movement keywords)
_GAZE_MAP: Dict[str, tuple] = {
    '向左看': ('servo1', 160), '往左看': ('servo1', 160),
    '向右看': ('servo1', 20),  '往右看': ('servo1', 20),
    '向上看': ('servo2', 30),  '往下看': ('servo2', 150),
    '看左边': ('servo1', 160), '看右边': ('servo1', 20),
    '看上面': ('servo2', 30),  '看下面': ('servo2', 150),
    '抬头': ('servo2', 30),    '低头': ('servo2', 150),
}

def _normalize_chinese_numerals(text: str) -> str:
    """Replace Chinese numeral characters with ASCII digits for regex matching."""
    result = text
    for cn, digit in _CN_NUM_MAP.items():
        result = result.replace(cn, digit)
    return result

# Pattern: direction word + number + optional unit
_RE_DURATION = re.compile(
    r'(' + '|'.join(re.escape(k) for k in _DIRECTION_MAP) + r')\s*(\d+)\s*(秒|s|seconds?)?',
    re.IGNORECASE
)
# Pattern: direction word only (no number) — exact match against direction map keys
_RE_DIRECTION_ONLY = re.compile(
    r'^(' + '|'.join(re.escape(k) for k in _DIRECTION_MAP) + r')$'
)
# Pattern: servo + number
_RE_SERVO = re.compile(r'舵机\s*([12])\s*[到至转]\s*(\d{1,3})\s*[度°]?')
# English patterns
_RE_EN_DURATION = re.compile(
    r'(forward|backward|go\s+forward|go\s+backward|move\s+forward|move\s+backward|go\s+ahead|go\s+back|turn\s+left|turn\s+right|go\s+left|go\s+right)\s+(\d+)\s*(seconds?|s)?',
    re.IGNORECASE
)
_RE_EN_DIRECTION = re.compile(
    r'^(forward|backward|go\s+forward|go\s+backward|move\s+forward|go\s+ahead|go\s+back|turn\s+left|turn\s+right|go\s+left|go\s+right|left|right)$',
    re.IGNORECASE
)
_RE_EN_STOP = re.compile(r'^(stop|halt|freeze)$', re.IGNORECASE)


def _prefilter_command(text: str) -> Optional[Dict[str, Any]]:
    """Intercept clear movement/stop/servo commands before calling AI.

    Returns a dict with action info for direct execution, or None to fall through to AI.
    """
    stripped = text.strip()

    # 1) Stop commands
    if stripped in _STOP_WORDS or _RE_EN_STOP.match(stripped):
        return {
            'action': 'control_robot',
            'command': 'stop',
            'explanation': '已停止' if _chinese_pattern.search(stripped) else 'Stopped.',
        }

    # 2) Gaze / view commands → servo (before movement keywords)
    for phrase, (servo_cmd, angle_val) in _GAZE_MAP.items():
        if phrase in stripped:
            return {
                'action': 'control_robot',
                'command': servo_cmd,
                'angle': angle_val,
                'explanation': f'好的，{phrase}',
            }

    # 3) Chinese direction + duration (normalize Chinese numerals first)
    normalized = _normalize_chinese_numerals(stripped)
    m = _RE_DURATION.search(normalized)
    if m:
        cmd = _DIRECTION_MAP[m.group(1)]
        dur = int(m.group(2))
        return {
            'action': 'control_robot',
            'command': cmd,
            'duration': dur,
            'explanation': f'好的，{m.group(1)}{dur}秒' if _chinese_pattern.search(stripped) else f'{cmd} for {dur}s',
        }

    # 4) Chinese direction only
    m = _RE_DIRECTION_ONLY.match(stripped)
    if m:
        cmd = _DIRECTION_MAP[m.group(1)]
        return {
            'action': 'control_robot',
            'command': cmd,
            'explanation': f'好的，{m.group(1)}',
        }

    # 5) English direction + duration
    m = _RE_EN_DURATION.search(stripped.lower())
    if m:
        raw_cmd = m.group(1).replace(' ', '_')
        cmd = _normalize_en_direction(raw_cmd)
        dur = int(m.group(2))
        return {
            'action': 'control_robot',
            'command': cmd,
            'duration': dur,
            'explanation': f'{cmd} for {dur}s',
        }

    # 6) English direction only
    if _RE_EN_DIRECTION.match(stripped.lower()):
        raw_cmd = stripped.lower().replace(' ', '_')
        cmd = _normalize_en_direction(raw_cmd)
        return {
            'action': 'control_robot',
            'command': cmd,
            'explanation': f'{cmd}.',
        }

    # 7) Servo commands
    m = _RE_SERVO.search(stripped)
    if m:
        servo_idx = m.group(1)
        angle = int(m.group(2))
        angle = max(0, min(180, angle))
        return {
            'action': 'control_robot',
            'command': f'servo{servo_idx}',
            'angle': angle,
            'explanation': f'舵机{servo_idx}已转到{angle}度',
        }

    return None


def _normalize_en_direction(raw: str) -> str:
    if 'forward' in raw or 'ahead' in raw:
        return 'forward'
    if 'backward' in raw or 'back' in raw:
        return 'backward'
    if 'left' in raw:
        return 'left'
    if 'right' in raw:
        return 'right'
    return 'stop'


# ---- Keyword detection for tool_choice forcing (Scheme B) ----

_MOVEMENT_KEYWORDS = [
    '前进', '后退', '左转', '右转', '往前', '往后', '向左', '向右',
    '移动', '走', '跑', '转', '停', '舵机', '云台', 'servo',
    'forward', 'backward', 'left', 'right', 'stop', 'halt', 'move', 'go',
]

_REMINDER_KEYWORDS = [
    '提醒', 'remind', '通知', 'notify', '闹钟', 'alarm', '定时',
]

_METHOD_VOICE_KEYWORDS = [
    '语音', 'voice', '播报', '说话', '扬声器', '喇叭', 'speaker',
]

_METHOD_EMAIL_KEYWORDS = [
    '邮件', 'email', '邮箱', '发邮件', 'mail',
]


def _detect_tool_choice(text: str) -> Optional[str]:
    """Detect which tool to force based on keywords. Returns None for auto."""
    lower = text.lower()
    for kw in _MOVEMENT_KEYWORDS:
        if kw in lower:
            return 'control_robot'
    for kw in _REMINDER_KEYWORDS:
        if kw in lower:
            has_voice = any(kw in lower for kw in _METHOD_VOICE_KEYWORDS)
            has_email = any(kw in lower for kw in _METHOD_EMAIL_KEYWORDS)
            if has_voice or has_email:
                return 'set_reminder'
            return None
    return None


def _get_kimi() -> 'KimiClient':
    global _kimi_client
    if _kimi_client is None:
        _kimi_client = KimiClient()  # type: ignore[assignment]
    return _kimi_client


async def _parse_and_execute_tags(reply_text: str, user_id: int) -> tuple:
    """Parse action tags in AI response. Returns (action, result_text_or_None)."""
    session = session_manager.get_or_create(user_id)

    # Parse [CMD:forward|backward|left|right|stop|servo1|servo2] [DUR:seconds] [ANG:degrees]
    cmd_match = re.search(r'\[CMD:(forward|backward|left|right|stop|servo1|servo2)\]', reply_text)
    if cmd_match:
        command = cmd_match.group(1)
        args: Dict[str, Any] = {"command": command}

        dur_match = re.search(r'\[DUR:(\d+(?:\.\d+)?)\]', reply_text)
        if dur_match:
            args["duration"] = float(dur_match.group(1))

        ang_match = re.search(r'\[ANG:(\d+(?:\.\d+)?)\]', reply_text)
        if ang_match:
            args["angle"] = float(ang_match.group(1))

        await _execute_control_robot(args, session)
        return ("control_robot", None)

    # Parse [WEATHER:city] — call tool and return result
    weather_match = re.search(r'\[WEATHER:([^\]]+)\]', reply_text)
    if weather_match:
        city = weather_match.group(1).strip()
        try:
            info = _get_weather().get_weather(city)
            session.add_message("assistant", info)
            return ("chat_reply", info)
        except Exception as e:
            logger.error(f"Weather tool error: {e}")
            return ("chat_reply", f"Sorry, couldn't get weather for {city}.")

    # Parse [NEWS]
    if re.search(r'\[NEWS\]', reply_text):
        try:
            info = _get_news().get_news("")
            session.add_message("assistant", info)
            return ("chat_reply", info)
        except Exception as e:
            logger.error(f"News tool error: {e}")
            return ("chat_reply", "Sorry, couldn't get news right now.")

    # Parse [JOKE]
    if re.search(r'\[JOKE\]', reply_text):
        try:
            info = get_joke()
            session.add_message("assistant", info)
            return ("chat_reply", info)
        except Exception as e:
            logger.error(f"Joke tool error: {e}")
            return ("chat_reply", "Sorry, couldn't get a joke right now.")

    # Parse [REMIND:text] [TIME:ISO] [METHOD:VOICE|EMAIL]
    remind_match = re.search(r'\[REMIND:(.+?)\]\s*\[TIME:(.+?)\]\s*\[METHOD:(VOICE|EMAIL)\]', reply_text)
    if remind_match:
        text = remind_match.group(1).strip()
        scheduled_time = remind_match.group(2).strip()
        method = remind_match.group(3).strip()
        java_url = os.environ.get("JAVA_API_URL", "http://localhost:8090")
        payload = {
            "userId": user_id,
            "text": text,
            "scheduledTime": scheduled_time,
            "method": method,
            "email": "",
            "enabled": True
        }
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                await client.post(
                    f"{java_url}/api/reminders",
                    json=payload
                )
                logger.info(f"Reminder created via AI chat: {text} at {scheduled_time}")
        except Exception as e:
            logger.error(f"Failed to create reminder: {e}")
        return ("set_reminder", None)

    return ("chat_reply", None)


async def handle_ai_chat(message: Dict[str, Any]):
    payload = message.get("payload", {})
    user_id = payload.get("user_id")
    user_text = payload.get("message", "").strip()
    user_email = payload.get("email", "")

    if not user_id or not user_text:
        await manager.send_to_web({
            "type": "ai_chat_response",
            "payload": {"text": "Please provide a valid message.", "action": "chat_reply"}
        })
        return

    session = session_manager.get_or_create(int(user_id))
    session.add_message("user", user_text)

    try:
        # ---- Scheme A: Pre-filter clear commands, skip AI entirely ----
        prefilter_result = _prefilter_command(user_text)
        if prefilter_result is not None:
            await _execute_control_robot(prefilter_result, session)
            return

        # ---- Scheme A-weather: Direct weather query ----
        if _WEATHER_KW.search(user_text):
            try:
                info: str = _get_weather().get_weather("")
                session.add_message("assistant", info)
                await manager.send_to_web({
                    "type": "ai_chat_response",
                    "payload": {"text": info, "action": "chat_reply"}
                })
                return
            except Exception:
                pass  # Fall through to AI

        # ---- Scheme A-news: Direct news query ----
        if _NEWS_KW.search(user_text):
            try:
                info = _get_news().get_news("")
                session.add_message("assistant", info)
                await manager.send_to_web({
                    "type": "ai_chat_response",
                    "payload": {"text": info, "action": "chat_reply"}
                })
                return
            except Exception:
                pass

        # ---- Scheme A-joke: Direct joke query ----
        if _JOKE_KW.search(user_text):
            try:
                info = get_joke()
                session.add_message("assistant", info)
                await manager.send_to_web({
                    "type": "ai_chat_response",
                    "payload": {"text": info, "action": "chat_reply"}
                })
                return
            except Exception:
                pass

        system_prompt = get_web_ai_system_prompt()
        if user_email:
            system_prompt += f"\n\nThe current user's email address is {user_email}. When setting EMAIL reminders for this user, always use this email address. Do NOT ask the user for their email."

        api_messages = [{"role": "system", "content": system_prompt}]
        api_messages.extend(session.get_messages())

        # ---- Scheme B: Plain text chat with response parsing ----
        kimi = _get_kimi()
        reply_text = kimi.chat_messages(api_messages)

        if not reply_text:
            reply_text = "Sorry, I didn't understand."

        # Parse and execute action tags in AI response
        action, tool_result = await _parse_and_execute_tags(reply_text, int(user_id))

        # Strip raw tag lines from displayed text
        clean_text = re.sub(r'\s*\[CMD:[^\]]+\](?:\s*\[DUR:\d+(?:\.\d+)?\])?(?:\s*\[ANG:\d+(?:\.\d+)?\])?\s*', ' ', reply_text)
        clean_text = re.sub(r'\s*\[(?:WEATHER|REMIND|NEWS|JOKE):[^\]]*\]\s*', ' ', clean_text)
        clean_text = re.sub(r'\s*\[TIME:[^\]]+\]\s*', ' ', clean_text)
        clean_text = re.sub(r'\s*\[METHOD:(?:VOICE|EMAIL)\]\s*', ' ', clean_text)
        clean_text = re.sub(r'\s+', ' ', clean_text).strip()

        display_text = tool_result if tool_result else (clean_text or reply_text)

        session.add_message("assistant", display_text)
        await manager.send_to_web({
            "type": "ai_chat_response",
            "payload": {"text": display_text, "action": action}
        })
    except Exception as e:
        logger.exception("AI chat error")
        if "401" in str(e) or "Unauthorized" in str(e):
            _kimi_client = None
        # Return a user-friendly error with the original message for retry
        error_text = f"⚠️ 回复失败，请点击重发\n（{str(e)[:80]}）"
        await manager.send_to_web({
            "type": "ai_chat_response",
            "payload": {
                "text": error_text,
                "action": "chat_reply",
                "error": True,
                "originalMessage": user_text
            }
        })


async def _execute_control_robot(args: Dict[str, Any], session):
    """Execute a robot control command and send responses. Shared by prefilter and AI tool-call paths."""
    command = args.get("command", "stop")
    angle = args.get("angle", 90)
    duration = args.get("duration")
    explanation = args.get("explanation", f"Executing {command}")

    if command not in VALID_COMMANDS:
        command = "stop"

    await manager.send_to_pi({
        "type": "command",
        "payload": {"command": command, "angle": angle}
    })

    if duration and isinstance(duration, (int, float)) and duration > 0 and command != "stop":
        async def _auto_stop(delay: float):
            await asyncio.sleep(delay)
            await manager.send_to_pi({
                "type": "command",
                "payload": {"command": "stop"}
            })

        asyncio.create_task(_auto_stop(float(duration)))

    session.add_message("assistant", explanation)
    await manager.send_to_web({
        "type": "ai_chat_response",
        "payload": {
            "text": explanation,
            "action": "control_robot",
            "data": {"command": command, "angle": angle}
        }
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
        await _execute_control_robot(args, session)

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
    # Compensate for stale system-prompt timestamp + API latency:
    # ensure scheduled_time is at least 5s in the future (Java has 60s grace period).
    try:
        tz = datetime.timezone(datetime.timedelta(hours=8))
        now = datetime.datetime.now(tz).replace(tzinfo=None)
        target = datetime.datetime.fromisoformat(scheduled_time)
        min_future = now + datetime.timedelta(seconds=5)
        if target < min_future:
            logger.warning("scheduled_time %s too close, adjusting to %s", scheduled_time, min_future.isoformat())
            scheduled_time = min_future.strftime("%Y-%m-%dT%H:%M:%S")
    except Exception:
        pass

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
