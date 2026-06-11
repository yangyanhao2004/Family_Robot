"""
Main routing logic for local chat, direct replies, and tool selection.
"""

import re
from dataclasses import dataclass
from enum import Enum
from typing import Optional, Tuple

from .ollama_client import OllamaClient
from .tool_definitions import SYSTEM_PROMPT, TOOLS


class ToolType(Enum):
    TIME = "get_current_time"
    WEATHER = "get_weather"
    NEWS = "get_news"
    SYSTEM_STATUS = "get_system_status"
    JOKE = "get_joke"
    CLOUD = "cloud_handoff"
    COMMAND = "control_robot"
    NONE = "none"


@dataclass
class RouterResult:
    """Result from the router."""

    tool: ToolType
    response: Optional[str]
    arguments: dict


class Router:
    """Routes user queries to direct replies, tools, or Ollama."""

    TIME_PHRASES = [
        "几点",
        "几点钟",
        "现在时间",
        "现在几点",
        "今天几号",
        "今天日期",
        "什么时间",
        "什么日期",
        "几点了",
    ]
    WEATHER_PHRASES = [
        "天气",
        "气温",
        "温度",
        "多少度",
        "冷不冷",
        "热不热",
        "下雨",
        "刮风",
    ]
    NEWS_PHRASES = [
        "新闻",
        "头条",
        "最近发生",
        "今天有什么",
        "最新消息",
        "时事",
    ]
    SYSTEM_PHRASES = [
        "系统状态",
        "你怎么样",
        "你的温度",
        "CPU温度",
        "健康检查",
        "身体如何",
        "你还好吗",
    ]
    JOKE_PHRASES = [
        "讲个笑话",
        "笑话",
        "逗我笑",
        "搞笑",
        "说个有意思的",
        "幽默",
    ]

    LOCAL_PHRASES = [
        "你好",
        "嗨",
        "嘿",
        "早上好",
        "下午好",
        "晚上好",
        "你好吗",
        "你是谁",
        "你是什么",
        "你在做什么",
        "你叫什么",
        "你的名字",
        "谢谢",
        "感谢",
        "再见",
        "拜拜",
        "晚安",
        "帮助",
        "你能做什么",
    ]

    DIRECT_RESPONSES = [
        (
            r"^(早上好|下午好|晚上好|你好|嗨|嘿)[！!。.]*$",
            "你好，我在这里陪着你。",
        ),
        (
            r"^(你好吗|你怎么样|最近好吗)\??$",
            "我挺好的，很高兴能和你聊聊。",
        ),
        (
            r"^(你在做什么|你在干嘛|你在干什么)\??$",
            "我在听着呢，随时可以和你聊天。",
        ),
        (
            r"^(你是谁|你是什么|你叫什么|你的名字是|你叫什么名字)\??$",
            "我是贾维斯，你的语音助手。",
        ),
        (
            r"^(谢谢|谢谢你|感谢|多谢)[！!。.]*$",
            "不客气。",
        ),
        (
            r"^(再见|拜拜|晚安|回见|明天见)[！!。.]*$",
            "再见，我会一直在这儿等你。",
        ),
        (
            r"^(帮助|你能做什么|你可以做什么|有什么功能)\??$",
            "我可以陪你聊天、告诉你时间、播报天气和新闻、还能查看系统状态。",
        ),
        (
            r"\b(我想你|我好想你|\b我好孤独\b|\b我很孤独\b)",
            "我在这里陪着你，你可以随时和我说话。",
        ),
        (
            r"\b(我难过|我不开心|我很伤心|我心情不好|\b我好难过\b)",
            "听到你这么说我很心疼。我会一直在这里陪着你。",
        ),
        (
            r"\b(我好累|我很累|我好疲惫|\b我压力大\b|\b我压力好大\b)",
            "你辛苦了。咱们慢慢来，一步一步走。",
        ),
        (
            r"\b(安慰我|安慰一下我|鼓励我)",
            "我在这里陪你，你不是一个人。",
        ),
        (
            r"\b(我爱你|我喜欢你)",
            "我也在乎你。",
        ),
    ]

    COMPOSABLE_CHAT_RESPONSES = [
        (
            r"\b(早上好|下午好|晚上好|你好|嗨|嘿)\b",
            "你好，我在这里陪着你。",
        ),
        (
            r"\b(你好吗|你怎么样|最近好吗)\b",
            "我挺好的，很高兴能和你聊聊。",
        ),
        (
            r"\b(你在做什么|你在干嘛|你在干什么)\b",
            "我在听着呢，随时可以和你聊天。",
        ),
        (
            r"\b(你是谁|你叫什么|你的名字|你是什么)\b",
            "我是贾维斯，你的语音助手。",
        ),
        (
            r"\b(帮助|你能做什么|有什么功能)\b",
            "我可以陪你聊天、告诉你时间、播报天气和新闻、还能查看系统状态。",
        ),
        (
            r"\b(谢谢|感谢)\b",
            "不客气。",
        ),
        (
            r"\b(再见|拜拜|晚安|回见)\b",
            "再见，我会一直在这儿等你。",
        ),
    ]

    EXPLICIT_SYSTEM_TOOL_PHRASES = [
        "系统状态",
        "CPU温度",
        "健康检查",
        "你的温度",
    ]

    CONTEXTLESS_CLARIFICATIONS = [
        (
            r"\b(她叫什么|他叫什么|那个名字|它的名字)\b",
            "如果你问的是我的名字，我叫贾维斯。如果是别人，请再告诉我一下。",
        ),
        (
            r"\b(刚才说的什么|你说什么|再说一遍|什么来着)\b",
            "我刚才可能没听清楚，请你再清楚地说一遍。",
        ),
        (
            r"\b(什么号码|什么数字|多少号)\b",
            "请你把号码清楚地再说一遍。",
        ),
    ]

    def __init__(
        self,
        ollama_client: OllamaClient,
        enable_local_llm_routing: bool = False,
        allow_cloud_handoff: bool = False,
    ):
        self.client = ollama_client
        self.enable_local_llm_routing = enable_local_llm_routing
        self.allow_cloud_handoff = allow_cloud_handoff
        self.conversation_history = []

    def _is_local_chat(self, user_input: str) -> bool:
        """Check if the input is simple enough for local handling."""
        user_lower = user_input.lower().strip()
        for phrase in self.LOCAL_PHRASES:
            if phrase in user_lower:
                return True

        words = user_lower.split()
        return len(words) <= 3 and "?" not in user_input

    def _extract_news_category(self, user_input: str) -> str:
        """Extract news category from user input."""
        user_lower = user_input.lower()
        categories = [
            "business",
            "entertainment",
            "health",
            "science",
            "sports",
            "technology",
        ]
        synonyms = {"tech": "technology", "sport": "sports", "medical": "health"}

        for synonym, category in synonyms.items():
            if synonym in user_lower:
                return category

        for category in categories:
            if category in user_lower:
                return category

        return ""

    def _extract_location(self, user_input: str, response_text: str) -> str:
        """Extract location from user input or model response."""
        match = re.search(
            r'location["\s=:]+["\']*([^"\'\]\s,]+)',
            response_text,
            re.IGNORECASE,
        )
        if match:
            return match.group(1)

        patterns = [
            r"weather (?:in|for|at) ([A-Za-z\s]+)",
            r"in ([A-Za-z]+)",
            r"([A-Z][a-z]+(?:\s[A-Z][a-z]+)*)",
        ]

        for pattern in patterns:
            match = re.search(pattern, user_input)
            if not match:
                continue
            location = match.group(1).strip()
            if location.lower() not in ["the", "is", "it", "what", "how", "like"]:
                return location

        return ""

    def _detect_tool_from_text(
        self,
        user_input: str,
        response_text: str,
    ) -> Tuple[ToolType, dict]:
        """
        Detect tool requests from user text and fallback model text.
        """
        user_lower = user_input.lower()
        response_lower = (response_text or "").lower()

        if "get_current_time" in response_lower:
            return ToolType.TIME, {}
        if "get_weather" in response_lower:
            return ToolType.WEATHER, {"location": self._extract_location(user_input, response_text)}
        if "get_news" in response_lower:
            return ToolType.NEWS, {"category": self._extract_news_category(user_input)}
        if "get_system_status" in response_lower:
            return ToolType.SYSTEM_STATUS, {}
        if "get_joke" in response_lower:
            return ToolType.JOKE, {}
        if "cloud_handoff" in response_lower:
            return ToolType.CLOUD, {"query": user_input}

        # ---- Command detection (robot movement/servo) ----
        # Split multi-step: "forward 1s and back 1s" -> ["forward 1s", "back 1s"]
        import re as _re2
        parts = _re2.split(r'\s+(?:and|然后|接着|之后|再)\s+', user_lower)
        cmd_results = []
        for part in parts:
            part = part.strip()
            if part:
                r = self._detect_command(part, part)
                if r is not None:
                    cmd_results.append(r)
        if cmd_results:
            # Merge durations from all steps
            merged = dict(cmd_results[0])
            if len(cmd_results) > 1:
                merged["steps"] = cmd_results
                merged["command"] = "multi"
                merged["explanation"] = "OK, executing " + ", ".join(
                    f"{c.get('command', '?')}" + (f" for {c.get('duration', 0)}s" if c.get('duration') else "")
                    for c in cmd_results
                )
            return ToolType.COMMAND, merged

        for phrase in self.TIME_PHRASES:
            if phrase in user_lower:
                return ToolType.TIME, {}
        for phrase in self.WEATHER_PHRASES:
            if phrase in user_lower:
                return ToolType.WEATHER, {"location": self._extract_location(user_input, "")}
        for phrase in self.NEWS_PHRASES:
            if phrase in user_lower:
                return ToolType.NEWS, {"category": self._extract_news_category(user_input)}
        for phrase in self.JOKE_PHRASES:
            if phrase in user_lower:
                return ToolType.JOKE, {}
        for phrase in self.SYSTEM_PHRASES:
            if phrase in user_lower:
                return ToolType.SYSTEM_STATUS, {}

        if self._is_local_chat(user_input):
            return ToolType.NONE, {}

        return ToolType.CLOUD, {"query": user_input}

    # ---- Robot command detection ----
    COMMAND_KEYWORDS = {
        'forward': ['forward', 'go forward', 'move forward', 'ahead', '前进', '往前', '向前'],
        'backward': ['backward', 'go back', 'move back', 'backwards', '后退', '往后', '向后', '退后'],
        'left': ['left', 'turn left', 'go left', '左转', '往左', '向左'],
        'right': ['right', 'turn right', 'go right', '右转', '往右', '向右'],
        'stop': ['stop', 'halt', 'freeze', '停', '停下', '停止'],
        'servo1': ['pan', 'horizontal', '水平'],
        'servo2': ['tilt', 'vertical', '垂直', '抬头', '低头'],
    }

    def _detect_command(self, user_lower: str, user_original: str) -> Optional[dict]:
        """Detect robot movement/servo commands. Returns args dict or None."""
        import re as _re

        for cmd, phrases in self.COMMAND_KEYWORDS.items():
            for phrase in phrases:
                if phrase in user_lower:
                    # Extract duration: "1 second", "2 seconds", "3s", "一秒", "两秒"
                    dur_match = _re.search(
                        r'(\d+)\s*(?:second|sec|s|秒)(?:s)?|'
                        r'(one|two|three|four|five|1|2|3|4|5)\s*(?:second|sec|s)(?:s)?|'
                        r'(一|二|三|四|五|两|1|2|3|4|5)\s*秒',
                        user_lower
                    )
                    duration = None
                    if dur_match:
                        num_str = dur_match.group(1) or dur_match.group(2) or dur_match.group(3)
                        num_map = {'one': 1, 'two': 2, 'three': 3, 'four': 4, 'five': 5,
                                   '一': 1, '二': 2, '三': 3, '四': 4, '五': 5, '两': 2}
                        duration = float(num_map.get(num_str, num_str or 0))
                    return {"command": cmd, "duration": duration, "explanation": f"OK, {cmd} for {duration}s" if duration else f"OK, {cmd}"}
        return None

    def _has_explicit_tool_request(self, user_lower: str) -> bool:
        """Detect clear tool requests that should override chat heuristics."""
        tool_phrases = (
            self.TIME_PHRASES
            + self.WEATHER_PHRASES
            + self.NEWS_PHRASES
            + self.JOKE_PHRASES
            + self.EXPLICIT_SYSTEM_TOOL_PHRASES
        )
        return any(phrase in user_lower for phrase in tool_phrases)

    def _direct_response_from_text(self, user_input: str) -> Optional[str]:
        """Return a direct instant response for low-compute chat."""
        user_lower = user_input.lower().strip()

        for pattern, response in self.DIRECT_RESPONSES:
            if re.search(pattern, user_lower):
                return response

        if self._has_explicit_tool_request(user_lower):
            return None

        responses = []
        for pattern, response in self.COMPOSABLE_CHAT_RESPONSES:
            if re.search(pattern, user_lower) and response not in responses:
                responses.append(response)

        if responses:
            return " ".join(responses[:2])

        return None

    def _clarify_without_context(self, user_input: str) -> Optional[str]:
        """Return a clarification when the query depends on missing context."""
        user_lower = user_input.lower().strip()

        for pattern, response in self.CONTEXTLESS_CLARIFICATIONS:
            if re.search(pattern, user_lower):
                return response

        words = user_lower.split()
        if len(words) <= 5 and any(
            token in user_lower
            for token in ["他", "她", "它", "那个", "那些", "这个", "这些"]
        ):
            return "我没有足够的上下文，请你在一个句子里说清楚。"

        return None

    def _fast_path_route(self, user_input: str) -> Optional[RouterResult]:
        """
        Handle obvious tools and common emotional chat without using Ollama.
        """
        direct_response = self._direct_response_from_text(user_input)
        if direct_response:
            return RouterResult(
                tool=ToolType.NONE,
                response=direct_response,
                arguments={},
            )

        tool_type, arguments = self._detect_tool_from_text(user_input, "")
        if tool_type in {
            ToolType.TIME,
            ToolType.WEATHER,
            ToolType.NEWS,
            ToolType.SYSTEM_STATUS,
            ToolType.JOKE,
        }:
            return RouterResult(
                tool=tool_type,
                response=None,
                arguments=arguments,
            )

        clarification = self._clarify_without_context(user_input)
        if clarification:
            return RouterResult(
                tool=ToolType.NONE,
                response=clarification,
                arguments={},
            )

        return None

    def _offline_chat_response(self, user_input: str) -> str:
        """Fallback response when Ollama is unavailable."""
        direct_response = self._direct_response_from_text(user_input)
        if direct_response:
            return direct_response

        clarification = self._clarify_without_context(user_input)
        if clarification:
            return clarification

        user_lower = user_input.lower()
        if "你在做什么" in user_lower or "你在干嘛" in user_lower:
            return "我在听着呢，随时可以和你聊天。"
        if (
            "你叫什么" in user_lower
            or "你的名字" in user_lower
            or "你是谁" in user_lower
            or "你是什么" in user_lower
        ):
            return "我是贾维斯，你的语音助手。"

        return (
            "我的本地语言模型目前不在线。"
            "你仍然可以问我时间、天气、新闻、笑话或者系统状态。"
        )

    def route(self, user_input: str) -> RouterResult:
        """Route user input to a direct response, tool, or Ollama."""
        fast_path = self._fast_path_route(user_input)
        if fast_path is not None:
            self.conversation_history.append({"role": "user", "content": user_input})
            if fast_path.response:
                self.conversation_history.append(
                    {"role": "assistant", "content": fast_path.response}
                )
            return fast_path

        if not self.enable_local_llm_routing:
            tool_type, arguments = self._detect_tool_from_text(user_input, "")
            self.conversation_history.append({"role": "user", "content": user_input})

            if tool_type == ToolType.CLOUD and not self.allow_cloud_handoff:
                response = self._offline_chat_response(user_input)
                self.conversation_history.append(
                    {"role": "assistant", "content": response}
                )
                return RouterResult(
                    tool=ToolType.NONE,
                    response=response,
                    arguments={},
                )

            return RouterResult(
                tool=tool_type,
                response=None,
                arguments=arguments,
            )

        if not self.client.is_available():
            tool_type, arguments = self._detect_tool_from_text(user_input, "")
            self.conversation_history.append({"role": "user", "content": user_input})

            if tool_type == ToolType.NONE:
                response = self._offline_chat_response(user_input)
                self.conversation_history.append(
                    {"role": "assistant", "content": response}
                )
                return RouterResult(
                    tool=ToolType.NONE,
                    response=response,
                    arguments={},
                )

            return RouterResult(
                tool=tool_type,
                response=None,
                arguments=arguments,
            )

        messages = [{"role": "system", "content": SYSTEM_PROMPT}]
        messages.extend(self.conversation_history[-8:])
        messages.append({"role": "user", "content": user_input})

        response = self.client.chat(messages, tools=TOOLS)

        if response.is_tool_call:
            tool_call = response.tool_calls[0]
            try:
                tool_type = ToolType(tool_call.name)
            except ValueError:
                tool_type = ToolType.NONE

            self.conversation_history.append({"role": "user", "content": user_input})
            return RouterResult(
                tool=tool_type,
                response=None,
                arguments=tool_call.arguments,
            )

        tool_type, arguments = self._detect_tool_from_text(user_input, response.content)
        self.conversation_history.append({"role": "user", "content": user_input})

        if tool_type == ToolType.NONE:
            self.conversation_history.append(
                {"role": "assistant", "content": response.content or ""}
            )
            return RouterResult(
                tool=ToolType.NONE,
                response=response.content,
                arguments={},
            )

        return RouterResult(
            tool=tool_type,
            response=None,
            arguments=arguments,
        )

    def set_cloud_handoff_enabled(self, enabled: bool):
        """Enable or disable direct cloud handoff for complex queries."""
        self.allow_cloud_handoff = enabled

    def clear_history(self):
        """Clear conversation history."""
        self.conversation_history = []
