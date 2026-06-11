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

    def chat_messages(self, messages: list, max_retries: int = 3) -> str:
        """Send multi-turn messages to Kimi and return the response.

        Retries on 429 (rate limit) with exponential backoff: 3s, 6s, 12s.
        """
        import time

        payload = {
            "model": "moonshot-v1-8k",
            "messages": messages,
            "stream": False,
        }
        for attempt in range(max_retries + 1):
            response = self.client.post(
                f"{self.BASE_URL}/chat/completions",
                json=payload,
            )
            if response.status_code == 429:
                body = response.text[:200]
                print(f"[cloud] 429 response: {body}")
                if attempt < max_retries:
                    wait = 3 * (2 ** attempt)
                    print(f"[cloud] retrying in {wait}s (attempt {attempt + 1}/{max_retries})")
                    time.sleep(wait)
                    continue
                # All retries exhausted
                raise RuntimeError(
                    f"Moonshot API 429 after {max_retries} retries. Response: {body}"
                )

            response.raise_for_status()
            return response.json()["choices"][0]["message"]["content"]
