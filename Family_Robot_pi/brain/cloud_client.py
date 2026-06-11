"""
Cloud API client — supports Moonshot (Kimi) and DeepSeek.

Set DEEPSEEK_API_KEY in .env to use DeepSeek (recommended).
Falls back to MOONSHOT_API_KEY for Moonshot.
"""

import httpx
from typing import Optional
from pathlib import Path
import os


class KimiClient:
    """Cloud AI client — auto-selects DeepSeek or Moonshot based on env vars."""

    @staticmethod
    def _detect_provider():
        """Return (base_url, model, api_key) for the best available provider."""
        # Prefer DeepSeek if key is set
        deepseek_key = os.getenv("DEEPSEEK_API_KEY")
        if deepseek_key:
            key_preview = deepseek_key[:7] + "..." if len(deepseek_key) > 10 else "???"
            print(f"[cloud] Using DeepSeek (key={key_preview}, len={len(deepseek_key)})")
            return ("https://api.deepseek.com/v1", "deepseek-chat", deepseek_key)

        # Fallback to Moonshot
        moonshot_key = os.getenv("MOONSHOT_API_KEY")
        if moonshot_key:
            key_preview = moonshot_key[:7] + "..." if len(moonshot_key) > 10 else "???"
            print(f"[cloud] Using Moonshot (key={key_preview}, len={len(moonshot_key)})")
            return ("https://api.moonshot.cn/v1", "moonshot-v1-8k", moonshot_key)

        raise ValueError("Set DEEPSEEK_API_KEY or MOONSHOT_API_KEY in .env")

    def __init__(
        self,
        api_key: Optional[str] = None,
        soul_path: Optional[str] = None,
    ):
        self.base_url, self.model, key = self._detect_provider()
        self.api_key = (api_key or key).strip()

        self.client = httpx.Client(
            timeout=60.0,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
        )
        print(f"[cloud] Endpoint: {self.base_url}  Model: {self.model}")

        self.soul_prompt = ""
        if soul_path and Path(soul_path).exists():
            self.soul_prompt = Path(soul_path).read_text()

    def chat(self, query: str) -> str:
        messages = []
        if self.soul_prompt:
            messages.append({"role": "system", "content": self.soul_prompt})
        messages.append({"role": "user", "content": query})
        return self.chat_messages(messages)

    def chat_messages(self, messages: list) -> str:
        payload = {
            "model": self.model,
            "messages": messages,
            "stream": False,
        }
        response = self.client.post(
            f"{self.base_url}/chat/completions",
            json=payload,
        )
        if response.status_code == 429:
            body = response.text[:200]
            print(f"[cloud] 429: {body}")
            raise RuntimeError("API rate limited. Wait 15 seconds and retry.")

        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"]
