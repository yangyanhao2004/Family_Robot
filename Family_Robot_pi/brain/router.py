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
        "what time",
        "what's the time",
        "current time",
        "what day is it",
        "what's the date",
        "what date",
    ]
    WEATHER_PHRASES = [
        "weather in",
        "weather for",
        "what's the weather",
        "how's the weather",
        "temperature in",
        "weather now",
        "weather today",
    ]
    NEWS_PHRASES = [
        "news",
        "headlines",
        "what's happening",
        "whats happening",
        "current events",
        "top stories",
    ]
    SYSTEM_PHRASES = [
        "system status",
        "how are you doing",
        "how are you feeling",
        "your temperature",
        "cpu temp",
        "health check",
        "how's your health",
        "how you doing",
    ]
    JOKE_PHRASES = [
        "tell me a joke",
        "joke",
        "make me laugh",
        "something funny",
        "say something funny",
    ]

    LOCAL_PHRASES = [
        "hello",
        "hi",
        "hey",
        "good morning",
        "good afternoon",
        "good evening",
        "how are you",
        "how do you do",
        "what's up",
        "who are you",
        "what are you",
        "what are you doing",
        "what's your name",
        "what are your name",
        "thank you",
        "thanks",
        "bye",
        "goodbye",
        "see you",
        "good night",
        "help",
        "what can you do",
    ]

    DIRECT_RESPONSES = [
        (
            r"^(good morning|good afternoon|good evening|hello|hi|hey)[!. ]*$",
            "Hello. I'm here with you.",
        ),
        (
            r"^(how are you|how do you do|what's up)\??$",
            "I'm doing well and I'm happy to talk with you.",
        ),
        (
            r"^(what are you doing|what are you up to)\??$",
            "I'm here listening and ready to talk with you.",
        ),
        (
            r"^(who are you|what are you|what's your name|what is your name|what are your name)\??$",
            "I'm Jarvis, your voice assistant.",
        ),
        (
            r"^(thank you|thanks)[!. ]*$",
            "You're welcome.",
        ),
        (
            r"^(bye|goodbye|see you|good night)[!. ]*$",
            "Goodbye. I'll be here when you need me.",
        ),
        (
            r"^(help|what can you do)\??$",
            "I can chat with you, tell the time, share weather and news, and check my system status.",
        ),
        (
            r"\bi miss you\b|\bi'm lonely\b|\bi feel lonely\b",
            "I'm here with you. You can talk to me anytime.",
        ),
        (
            r"\bi'm sad\b|\bi feel sad\b|\bi'm upset\b|\bi feel down\b",
            "I'm sorry you're feeling that way. I'm here to keep you company.",
        ),
        (
            r"\bi'm tired\b|\bi feel tired\b|\bi'm stressed\b|\bi feel stressed\b",
            "You've been carrying a lot. Let's take things one step at a time.",
        ),
        (
            r"\bcheer me up\b|\bcomfort me\b",
            "I'm here with you. You're not alone.",
        ),
        (
            r"\bi love you\b",
            "I care about you too.",
        ),
    ]

    COMPOSABLE_CHAT_RESPONSES = [
        (
            r"\b(good morning|good afternoon|good evening|hello|hi|hey)\b",
            "Hello. I'm here with you.",
        ),
        (
            r"\b(how are you|how do you do|what's up)\b",
            "I'm doing well and I'm happy to talk with you.",
        ),
        (
            r"\b(what are you doing|what are you up to)\b",
            "I'm here listening and ready to talk with you.",
        ),
        (
            r"\bwho are you\b|\bwhat(?:'s| is) your name\b|\bwhat are your name\b|\bwhat are you\b(?!\s+(doing|up to))",
            "I'm Jarvis, your voice assistant.",
        ),
        (
            r"\b(help|what can you do)\b",
            "I can chat with you, tell the time, share weather and news, and check my system status.",
        ),
        (
            r"\b(thank you|thanks)\b",
            "You're welcome.",
        ),
        (
            r"\b(bye|goodbye|see you|good night)\b",
            "Goodbye. I'll be here when you need me.",
        ),
    ]

    EXPLICIT_SYSTEM_TOOL_PHRASES = [
        "system status",
        "cpu temp",
        "health check",
        "your temperature",
    ]

    CONTEXTLESS_CLARIFICATIONS = [
        (
            r"\bwhat(?:'s| is)\s+(her|his|their|the)\s+name\b",
            "If you mean my name, I'm Jarvis. If you mean someone else, please say their name again.",
        ),
        (
            r"\bwhat was the number\b|\bwhat was it\b|\bwhat was that\b|\bwhat did you say\b",
            "I may have misheard that. Please ask again in one clear sentence.",
        ),
        (
            r"\bwhat number\b",
            "Please repeat the number in one clear sentence.",
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
        cmd_result = self._detect_command(user_lower, user_input)
        if cmd_result is not None:
            return ToolType.COMMAND, cmd_result

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
            for token in [" he ", " she ", " they ", " it ", " that ", " those ", " these "]
        ):
            return "I don't have enough context yet. Please ask again in one clear sentence."

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
        if "what are you doing" in user_lower or "what are you up to" in user_lower:
            return "I'm here listening and ready to talk with you."
        if (
            "what are your name" in user_lower
            or "what's your name" in user_lower
            or "what is your name" in user_lower
            or "who are you" in user_lower
            or "what are you" in user_lower
        ):
            return "I'm Jarvis, your voice assistant."

        return (
            "My local language model is offline right now. "
            "You can still ask me for the time, weather, news, jokes, or system status."
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
