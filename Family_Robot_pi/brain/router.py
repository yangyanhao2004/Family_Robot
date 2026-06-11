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
        "\u51e0\u70b9",
        "\u51e0\u70b9\u949f",
        "\u73b0\u5728\u65f6\u95f4",
        "\u73b0\u5728\u51e0\u70b9",
        "\u4eca\u5929\u51e0\u53f7",
        "\u4eca\u5929\u65e5\u671f",
        "\u4ec0\u4e48\u65f6\u95f4",
        "\u4ec0\u4e48\u65e5\u671f",
        "\u51e0\u70b9\u4e86",
    ]
    WEATHER_PHRASES = [
        "\u5929\u6c14",
        "\u6c14\u6e29",
        "\u6e29\u5ea6",
        "\u591a\u5c11\u5ea6",
        "\u51b7\u4e0d\u51b7",
        "\u70ed\u4e0d\u70ed",
        "\u4e0b\u96e8",
        "\u522e\u98ce",
    ]
    NEWS_PHRASES = [
        "\u65b0\u95fb",
        "\u5934\u6761",
        "\u6700\u8fd1\u53d1\u751f",
        "\u4eca\u5929\u6709\u4ec0\u4e48",
        "\u6700\u65b0\u6d88\u606f",
        "\u65f6\u4e8b",
    ]
    SYSTEM_PHRASES = [
        "\u7cfb\u7edf\u72b6\u6001",
        "\u4f60\u600e\u4e48\u6837",
        "\u4f60\u7684\u6e29\u5ea6",
        "CPU\u6e29\u5ea6",
        "\u5065\u5eb7\u68c0\u67e5",
        "\u8eab\u4f53\u5982\u4f55",
        "\u4f60\u8fd8\u597d\u5417",
    ]
    JOKE_PHRASES = [
        "\u8bb2\u4e2a\u7b11\u8bdd",
        "\u7b11\u8bdd",
        "\u9017\u6211\u7b11",
        "\u641e\u7b11",
        "\u8bf4\u4e2a\u6709\u610f\u601d\u7684",
        "\u5e7d\u9ed8",
    ]

    LOCAL_PHRASES = [
        "\u4f60\u597d",
        "\u55e8",
        "\u563f",
        "\u65e9\u4e0a\u597d",
        "\u4e0b\u5348\u597d",
        "\u665a\u4e0a\u597d",
        "\u4f60\u597d\u5417",
        "\u4f60\u662f\u8c01",
        "\u4f60\u662f\u4ec0\u4e48",
        "\u4f60\u5728\u505a\u4ec0\u4e48",
        "\u4f60\u53eb\u4ec0\u4e48",
        "\u4f60\u7684\u540d\u5b57",
        "\u8c22\u8c22",
        "\u611f\u8c22",
        "\u518d\u89c1",
        "\u62dc\u62dc",
        "\u665a\u5b89",
        "\u5e2e\u52a9",
        "\u4f60\u80fd\u505a\u4ec0\u4e48",
    ]

    DIRECT_RESPONSES = [
        (
            r"^(\u65e9\u4e0a\u597d|\u4e0b\u5348\u597d|\u665a\u4e0a\u597d|\u4f60\u597d|\u55e8|\u563f)[！!。.]*$",
            "\u4f60\u597d，\u6211\u5728\u8fd9\u91cc\u966a\u7740\u4f60。",
        ),
        (
            r"^(\u4f60\u597d\u5417|\u4f60\u600e\u4e48\u6837|\u6700\u8fd1\u597d\u5417)\??$",
            "\u6211\u633a\u597d\u7684，\u5f88\u9ad8\u5174\u80fd\u548c\u4f60\u804a\u804a。",
        ),
        (
            r"^(\u4f60\u5728\u505a\u4ec0\u4e48|\u4f60\u5728\u5e72\u561b|\u4f60\u5728\u5e72\u4ec0\u4e48)\??$",
            "\u6211\u5728\u542c\u7740\u5462，\u968f\u65f6\u53ef\u4ee5\u548c\u4f60\u804a\u5929。",
        ),
        (
            r"^(\u4f60\u662f\u8c01|\u4f60\u662f\u4ec0\u4e48|\u4f60\u53eb\u4ec0\u4e48|\u4f60\u7684\u540d\u5b57\u662f|\u4f60\u53eb\u4ec0\u4e48\u540d\u5b57)\??$",
            "\u6211\u662f\u8d3e\u7ef4\u65af，\u4f60\u7684\u8bed\u97f3\u52a9\u624b。",
        ),
        (
            r"^(\u8c22\u8c22|\u8c22\u8c22\u4f60|\u611f\u8c22|\u591a\u8c22)[！!。.]*$",
            "\u4e0d\u5ba2\u6c14。",
        ),
        (
            r"^(\u518d\u89c1|\u62dc\u62dc|\u665a\u5b89|\u56de\u89c1|\u660e\u5929\u89c1)[！!。.]*$",
            "\u518d\u89c1，\u6211\u4f1a\u4e00\u76f4\u5728\u8fd9\u513f\u7b49\u4f60。",
        ),
        (
            r"^(\u5e2e\u52a9|\u4f60\u80fd\u505a\u4ec0\u4e48|\u4f60\u53ef\u4ee5\u505a\u4ec0\u4e48|\u6709\u4ec0\u4e48\u529f\u80fd)\??$",
            "\u6211\u53ef\u4ee5\u966a\u4f60\u804a\u5929、\u544a\u8bc9\u4f60\u65f6\u95f4、\u64ad\u62a5\u5929\u6c14\u548c\u65b0\u95fb、\u8fd8\u80fd\u67e5\u770b\u7cfb\u7edf\u72b6\u6001。",
        ),
        (
            r"\b(\u6211\u60f3\u4f60|\u6211\u597d\u60f3\u4f60|\b\u6211\u597d\u5b64\u72ec\b|\b\u6211\u5f88\u5b64\u72ec\b)",
            "\u6211\u5728\u8fd9\u91cc\u966a\u7740\u4f60，\u4f60\u53ef\u4ee5\u968f\u65f6\u548c\u6211\u8bf4\u8bdd。",
        ),
        (
            r"\b(\u6211\u96be\u8fc7|\u6211\u4e0d\u5f00\u5fc3|\u6211\u5f88\u4f24\u5fc3|\u6211\u5fc3\u60c5\u4e0d\u597d|\b\u6211\u597d\u96be\u8fc7\b)",
            "\u542c\u5230\u4f60\u8fd9\u4e48\u8bf4\u6211\u5f88\u5fc3\u75bc。\u6211\u4f1a\u4e00\u76f4\u5728\u8fd9\u91cc\u966a\u7740\u4f60。",
        ),
        (
            r"\b(\u6211\u597d\u7d2f|\u6211\u5f88\u7d2f|\u6211\u597d\u75b2\u60eb|\b\u6211\u538b\u529b\u5927\b|\b\u6211\u538b\u529b\u597d\u5927\b)",
            "\u4f60\u8f9b\u82e6\u4e86。\u54b1\u4eec\u6162\u6162\u6765，\u4e00\u6b65\u4e00\u6b65\u8d70。",
        ),
        (
            r"\b(\u5b89\u6170\u6211|\u5b89\u6170\u4e00\u4e0b\u6211|\u9f13\u52b1\u6211)",
            "\u6211\u5728\u8fd9\u91cc\u966a\u4f60，\u4f60\u4e0d\u662f\u4e00\u4e2a\u4eba。",
        ),
        (
            r"\b(\u6211\u7231\u4f60|\u6211\u559c\u6b22\u4f60)",
            "\u6211\u4e5f\u5728\u4e4e\u4f60。",
        ),
    ]

    COMPOSABLE_CHAT_RESPONSES = [
        (
            r"\b(\u65e9\u4e0a\u597d|\u4e0b\u5348\u597d|\u665a\u4e0a\u597d|\u4f60\u597d|\u55e8|\u563f)\b",
            "\u4f60\u597d，\u6211\u5728\u8fd9\u91cc\u966a\u7740\u4f60。",
        ),
        (
            r"\b(\u4f60\u597d\u5417|\u4f60\u600e\u4e48\u6837|\u6700\u8fd1\u597d\u5417)\b",
            "\u6211\u633a\u597d\u7684，\u5f88\u9ad8\u5174\u80fd\u548c\u4f60\u804a\u804a。",
        ),
        (
            r"\b(\u4f60\u5728\u505a\u4ec0\u4e48|\u4f60\u5728\u5e72\u561b|\u4f60\u5728\u5e72\u4ec0\u4e48)\b",
            "\u6211\u5728\u542c\u7740\u5462，\u968f\u65f6\u53ef\u4ee5\u548c\u4f60\u804a\u5929。",
        ),
        (
            r"\b(\u4f60\u662f\u8c01|\u4f60\u53eb\u4ec0\u4e48|\u4f60\u7684\u540d\u5b57|\u4f60\u662f\u4ec0\u4e48)\b",
            "\u6211\u662f\u8d3e\u7ef4\u65af，\u4f60\u7684\u8bed\u97f3\u52a9\u624b。",
        ),
        (
            r"\b(\u5e2e\u52a9|\u4f60\u80fd\u505a\u4ec0\u4e48|\u6709\u4ec0\u4e48\u529f\u80fd)\b",
            "\u6211\u53ef\u4ee5\u966a\u4f60\u804a\u5929、\u544a\u8bc9\u4f60\u65f6\u95f4、\u64ad\u62a5\u5929\u6c14\u548c\u65b0\u95fb、\u8fd8\u80fd\u67e5\u770b\u7cfb\u7edf\u72b6\u6001。",
        ),
        (
            r"\b(\u8c22\u8c22|\u611f\u8c22)\b",
            "\u4e0d\u5ba2\u6c14。",
        ),
        (
            r"\b(\u518d\u89c1|\u62dc\u62dc|\u665a\u5b89|\u56de\u89c1)\b",
            "\u518d\u89c1，\u6211\u4f1a\u4e00\u76f4\u5728\u8fd9\u513f\u7b49\u4f60。",
        ),
    ]

    EXPLICIT_SYSTEM_TOOL_PHRASES = [
        "\u7cfb\u7edf\u72b6\u6001",
        "CPU\u6e29\u5ea6",
        "\u5065\u5eb7\u68c0\u67e5",
        "\u4f60\u7684\u6e29\u5ea6",
    ]

    CONTEXTLESS_CLARIFICATIONS = [
        (
            r"\b(\u5979\u53eb\u4ec0\u4e48|\u4ed6\u53eb\u4ec0\u4e48|\u90a3\u4e2a\u540d\u5b57|\u5b83\u7684\u540d\u5b57)\b",
            "\u5982\u679c\u4f60\u95ee\u7684\u662f\u6211\u7684\u540d\u5b57，\u6211\u53eb\u8d3e\u7ef4\u65af。\u5982\u679c\u662f\u522b\u4eba，\u8bf7\u518d\u544a\u8bc9\u6211\u4e00\u4e0b。",
        ),
        (
            r"\b(\u521a\u624d\u8bf4\u7684\u4ec0\u4e48|\u4f60\u8bf4\u4ec0\u4e48|\u518d\u8bf4\u4e00\u904d|\u4ec0\u4e48\u6765\u7740)\b",
            "\u6211\u521a\u624d\u53ef\u80fd\u6ca1\u542c\u6e05\u695a，\u8bf7\u4f60\u518d\u6e05\u695a\u5730\u8bf4\u4e00\u904d。",
        ),
        (
            r"\b(\u4ec0\u4e48\u53f7\u7801|\u4ec0\u4e48\u6570\u5b57|\u591a\u5c11\u53f7)\b",
            "\u8bf7\u4f60\u628a\u53f7\u7801\u6e05\u695a\u5730\u518d\u8bf4\u4e00\u904d。",
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

    # Traditional → Simplified Chinese mapping for keyword matching.
    # whisper.cpp zh model outputs Traditional; our keywords are Simplified.
    _T2S = str.maketrans(
        "氣麼幾嗎時聞條頭發樣"
        "關於會過來對體點號電"
        "話見說聽寫讓業東衝國"
        "絕綜變熱滿灑獲從當兩"
        "無舉處謂樂營僅嚴回廚"
        "請設計難重準單",
        "气么几吗时闻条头发样"
        "关于会过来对体点号电"
        "话见说听写让业东冲国"
        "绝综变热满洒获从当两"
        "无举处谓乐营仅严回厨"
        "请设计难重准单",
    )

    @staticmethod
    def _simplify(text: str) -> str:
        """Convert common Traditional Chinese chars to Simplified for matching."""
        return text.translate(Router._T2S)

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
        """Extract location from user input or model response (Chinese + English)."""
        match = re.search(
            r'location["\s=:]+["\']*([^"\'\]\s,]+)',
            response_text,
            re.IGNORECASE,
        )
        if match:
            return match.group(1)

        # Chinese patterns: "\u5317\u4eac\u7684\u5929\u6c14", "\u5317\u4eac\u5929\u6c14", "\u4e0a\u6d77\u600e\u4e48\u6837"
        cn_patterns = [
            r"([\u4e00-\u9fa5]{2,6})(?:\u7684)(?:\u5929\u6c14|\u6c14\u6e29|\u6e29\u5ea6|\u600e\u4e48\u6837|\u5982\u4f55)",
            r"(?:\u5929\u6c14|\u6c14\u6e29|\u6e29\u5ea6)(?:\u5728|\u5173\u4e8e)?([\u4e00-\u9fa5]{2,6})",
            r"([\u4e00-\u9fa5]{2,6})(?:\u5929\u6c14|\u6c14\u6e29|\u6e29\u5ea6)",
        ]
        for pattern in cn_patterns:
            m = re.search(pattern, user_input)
            if m:
                loc = m.group(1).strip()
                if loc not in ("\u4eca\u5929", "\u660e\u5929", "\u73b0\u5728", "\u90a3\u91cc", "\u54ea\u91cc", "\u8fd9\u513f", "\u8fd9\u91cc"):
                    return loc

        # English patterns
        en_patterns = [
            r"weather (?:in|for|at) ([A-Za-z\s]+)",
            r"in ([A-Za-z]+)",
            r"([A-Z][a-z]+(?:\s[A-Z][a-z]+)*)",
        ]
        for pattern in en_patterns:
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
        user_lower = self._simplify(user_input.lower())
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
        parts = _re2.split(r'\s+(?:and|\u7136\u540e|\u63a5\u7740|\u4e4b\u540e|\u518d)\s+', user_lower)
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
        'forward': ['forward', 'go forward', 'move forward', 'ahead', '\u524d\u8fdb', '\u5f80\u524d', '\u5411\u524d'],
        'backward': ['backward', 'go back', 'move back', 'backwards', '\u540e\u9000', '\u5f80\u540e', '\u5411\u540e', '\u9000\u540e'],
        'left': ['left', 'turn left', 'go left', '\u5de6\u8f6c', '\u5f80\u5de6', '\u5411\u5de6'],
        'right': ['right', 'turn right', 'go right', '\u53f3\u8f6c', '\u5f80\u53f3', '\u5411\u53f3'],
        'stop': ['stop', 'halt', 'freeze', '\u505c', '\u505c\u4e0b', '\u505c\u6b62'],
        'servo1': ['pan', 'horizontal', '\u6c34\u5e73'],
        'servo2': ['tilt', 'vertical', '\u5782\u76f4', '\u62ac\u5934', '\u4f4e\u5934'],
    }

    def _detect_command(self, user_lower: str, user_original: str) -> Optional[dict]:
        """Detect robot movement/servo commands. Returns args dict or None."""
        import re as _re

        for cmd, phrases in self.COMMAND_KEYWORDS.items():
            for phrase in phrases:
                if phrase in user_lower:
                    # Extract duration: "1 second", "2 seconds", "3s", "\u4e00\u79d2", "\u4e24\u79d2"
                    dur_match = _re.search(
                        r'(\d+)\s*(?:second|sec|s|\u79d2)(?:s)?|'
                        r'(one|two|three|four|five|1|2|3|4|5)\s*(?:second|sec|s)(?:s)?|'
                        r'(\u4e00|\u4e8c|\u4e09|\u56db|\u4e94|\u4e24|1|2|3|4|5)\s*\u79d2',
                        user_lower
                    )
                    duration = None
                    if dur_match:
                        num_str = dur_match.group(1) or dur_match.group(2) or dur_match.group(3)
                        num_map = {'one': 1, 'two': 2, 'three': 3, 'four': 4, 'five': 5,
                                   '\u4e00': 1, '\u4e8c': 2, '\u4e09': 3, '\u56db': 4, '\u4e94': 5, '\u4e24': 2}
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
            for token in ["\u4ed6", "\u5979", "\u5b83", "\u90a3\u4e2a", "\u90a3\u4e9b", "\u8fd9\u4e2a", "\u8fd9\u4e9b"]
        ):
            return "\u6211\u6ca1\u6709\u8db3\u591f\u7684\u4e0a\u4e0b\u6587，\u8bf7\u4f60\u5728\u4e00\u4e2a\u53e5\u5b50\u91cc\u8bf4\u6e05\u695a。"

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
        if "\u4f60\u5728\u505a\u4ec0\u4e48" in user_lower or "\u4f60\u5728\u5e72\u561b" in user_lower:
            return "\u6211\u5728\u542c\u7740\u5462，\u968f\u65f6\u53ef\u4ee5\u548c\u4f60\u804a\u5929。"
        if (
            "\u4f60\u53eb\u4ec0\u4e48" in user_lower
            or "\u4f60\u7684\u540d\u5b57" in user_lower
            or "\u4f60\u662f\u8c01" in user_lower
            or "\u4f60\u662f\u4ec0\u4e48" in user_lower
        ):
            return "\u6211\u662f\u8d3e\u7ef4\u65af，\u4f60\u7684\u8bed\u97f3\u52a9\u624b。"

        return (
            "\u6211\u7684\u672c\u5730\u8bed\u8a00\u6a21\u578b\u76ee\u524d\u4e0d\u5728\u7ebf。"
            "\u4f60\u4ecd\u7136\u53ef\u4ee5\u95ee\u6211\u65f6\u95f4、\u5929\u6c14、\u65b0\u95fb、\u7b11\u8bdd\u6216\u8005\u7cfb\u7edf\u72b6\u6001。"
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
