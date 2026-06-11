"""
Cloud API client for Kimi K2 (Moonshot).
"""

import httpx
from typing import Optional
from pathlib import Path
import os


class KimiClient:
    """Client for Kimi K2 (Moonshot) API."""

    BASE_URL = "https://api.moonshot.cn/v1"

    def __init__(
        self,
        api_key: Optional[str] = None,
        soul_path: Optional[str] = None
    ):
        self.api_key = api_key or os.getenv("MOONSHOT_API_KEY")
        if not self.api_key:
            raise ValueError("Moonshot API key required")

        self.client = httpx.Client(
            timeout=60.0,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
        )

        # Load cloud soul/personality
        self.soul_prompt = ""
        if soul_path and Path(soul_path).exists():
            self.soul_prompt = Path(soul_path).read_text()

    def chat(self, query: str) -> str:
        """Send single-turn query to Kimi and return the response."""
        messages = []

        if self.soul_prompt:
            messages.append({
                "role": "system",
                "content": self.soul_prompt
            })

        messages.append({
            "role": "user",
            "content": query
        })

        return self.chat_messages(messages)

    def chat_messages(self, messages: list) -> str:
        """Send multi-turn messages to Kimi and return the response.

        Does NOT retry on 429 — retrying burns the rate-limit quota faster.
        The caller (web/voice) should surface a clear wait-and-retry message.
        """
        payload = {
            "model": "moonshot-v1-32k",
            "messages": messages,
            "stream": False,
        }
        response = self.client.post(
            f"{self.BASE_URL}/chat/completions",
            json=payload,
        )
        if response.status_code == 429:
            body = response.text[:200]
            print(f"[cloud] 429: {body}")
            raise RuntimeError("Moonshot API rate limited. Wait 15 seconds and retry.")

        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"]
