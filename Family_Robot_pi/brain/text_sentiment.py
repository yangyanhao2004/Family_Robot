"""
Chinese text sentiment analysis — keyword-based, zero-dependency, < 1ms.

Covers positive/negative/sad/angry/fearful via weighted keyword matching.
"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class SentimentResult:
    label: str       # "happy", "sad", "angry", "fearful", "neutral"
    polarity: float  # -1.0 (negative) to +1.0 (positive)
    confidence: float  # 0–1


class TextSentiment:
    """Heuristic Chinese sentiment from keyword presence and weights."""

    # Weighted emotion keywords. Format: (word, weight) where weight > 0
    # Keywords cover both Simplified and Traditional Chinese (whisper.cpp outputs
    # Traditional with -l zh, but _simplify is called before analyze in orchestrator).
    HAPPY = [
        ("开心", 2), ("高兴", 2), ("快乐", 2), ("太棒", 3), ("太好了", 3),
        ("喜欢", 2), ("爱你", 3), ("真好", 2), ("幸福", 3), ("哈哈", 3),
        ("不错", 1), ("舒服", 1), ("满足", 2), ("激动", 2), ("期待", 1),
        ("好开心", 3), ("真开心", 3), ("爽", 2), ("漂亮", 1), ("好极了", 3),
        ("很棒", 2), ("厉害", 2), ("赞", 2), ("牛逼", 2), ("给力", 2),
    ]

    SAD = [
        ("难过", 3), ("伤心", 3), ("想哭", 3), ("好累", 2), ("孤独", 3),
        ("寂寞", 3), ("失望", 2), ("无助", 2), ("委屈", 2), ("心酸", 3),
        ("疼", 1), ("痛", 1), ("好痛", 3), ("崩溃", 3), ("绝望", 3),
        ("抑郁", 3), ("低落", 2), ("不开心", 2), ("想死", 3), ("没意思", 2),
        ("无聊", 1), ("睡不着", 2), ("好烦", 1), ("太累", 2), ("疲惫", 2),
    ]

    ANGRY = [
        ("气死", 3), ("滚", 2), ("混蛋", 3), ("讨厌", 2), ("烦死", 3),
        ("别烦", 3), ("闭嘴", 3), ("欠揍", 3), ("操", 3), ("妈的", 3),
        ("气人", 3), ("可恶", 2), ("恶心", 2), ("废物", 3), ("愚蠢", 2),
        ("白痴", 3), ("什么玩意", 3), ("受不了", 2), ("我靠", 2),
        ("去死", 3), ("垃圾", 2), ("烂", 1), ("差劲", 2), ("太过分", 2),
    ]

    FEARFUL = [
        ("害怕", 3), ("好怕", 3), ("恐怖", 3), ("吓死", 3), ("担心", 2),
        ("焦虑", 3), ("紧张", 2), ("不安", 2), ("惊慌", 3), ("恐惧", 3),
        ("不敢", 1), ("吓人", 2), ("危险", 2), ("可怕", 3), ("糟糕", 1),
    ]

    # Domain-specific context: whispering or sing-song voice often mis-detected
    # as neutral.  Text helps here.

    @classmethod
    def analyze(cls, text: str) -> SentimentResult:
        """Analyze sentiment of Chinese text."""
        if not text or not text.strip():
            return SentimentResult("neutral", 0.0, 0.5)

        scores = {"happy": 0.0, "sad": 0.0, "angry": 0.0, "fearful": 0.0}

        for kw, w in cls.HAPPY:
            if kw in text:
                scores["happy"] += w
        for kw, w in cls.SAD:
            if kw in text:
                scores["sad"] += w
        for kw, w in cls.ANGRY:
            if kw in text:
                scores["angry"] += w
        for kw, w in cls.FEARFUL:
            if kw in text:
                scores["fearful"] += w

        # Find max-emotion category
        best_label = max(scores, key=scores.get)
        best_score = scores[best_label]

        if best_score < 2:
            return SentimentResult("neutral", 0.0, 0.60)

        # Confidence: logarithmic scaling to avoid over-fitting on single keyword
        confidence = min(0.95, 0.55 + best_score * 0.08)

        # Polarity: happy > 0, sad/angry/fearful < 0
        polarity = 0.0
        if best_label == "happy":
            polarity = min(1.0, best_score * 0.2)
        elif best_label in ("sad", "angry", "fearful"):
            polarity = max(-1.0, -best_score * 0.2)

        return SentimentResult(best_label, polarity, confidence)


def fuse_emotions(acoustic_label: str, ac_conf: float,
                  text_label: str, tx_conf: float) -> tuple:
    """
    Fuse acoustic and text emotion into a single label and confidence.

    Strategy:
    - If both agree → high confidence
    - If text has strong signal → text wins (text is more reliable)
    - If neither has strong signal → neutral
    """
    if ac_conf < 0.55 and tx_conf < 0.55:
        return "neutral", 0.50

    # Text-override: if text is confident, it wins
    if tx_conf >= 0.65:
        return text_label, tx_conf

    # Acoustic-only: if text is neutral and acoustic has signal
    if ac_conf >= 0.60 and text_label == "neutral":
        return acoustic_label, ac_conf

    # Agreement bonus
    if acoustic_label == text_label:
        combined_conf = min(0.95, (ac_conf + tx_conf) / 2 + 0.15)
        return text_label, combined_conf

    # Default to whichever has higher confidence
    if ac_conf >= tx_conf:
        return acoustic_label, ac_conf
    else:
        return text_label, tx_conf
