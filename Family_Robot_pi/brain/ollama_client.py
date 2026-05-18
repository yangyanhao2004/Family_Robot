"""
Ollama API client with tool calling support.
"""

import httpx
import json
from typing import Optional, Dict, Any, List
from dataclasses import dataclass


@dataclass
class ToolCall:
    """Represents a tool call from the model."""
    name: str
    arguments: Dict[str, Any]


@dataclass
class ChatResponse:
    """Response from chat completion."""
    content: Optional[str]
    tool_calls: List[ToolCall]
    is_tool_call: bool


class OllamaClient:
    """Client for Ollama API with tool calling."""

    def __init__(
        self,
        base_url: str = "http://localhost:11434",
        model: str = "qwen2.5:1.5b",
        timeout: float = 120.0,
        num_predict: int = 128,
        num_ctx: int = 1024,
        temperature: float = 0.5,
        keep_alive: str = "15m"
    ):
        self.base_url = base_url
        self.model = model
        self.client = httpx.Client(timeout=timeout)
        self.num_predict = num_predict
        self.num_ctx = num_ctx
        self.temperature = temperature
        self.keep_alive = keep_alive

    def chat(
        self,
        messages: List[Dict[str, str]],
        tools: Optional[List[Dict]] = None,
        stream: bool = False
    ) -> ChatResponse:
        """
        Send chat completion request with optional tools.
        
        Args:
            messages: List of message dicts with 'role' and 'content'
            tools: Optional list of tool definitions
            stream: Whether to stream the response
        
        Returns:
            ChatResponse with content and/or tool calls
        """
        payload = {
            "model": self.model,
            "messages": messages,
            "stream": stream,
            "options": {
                "temperature": self.temperature,
                "num_predict": self.num_predict,
                "num_ctx": self.num_ctx
            },
            "keep_alive": self.keep_alive
        }

        if tools:
            payload["tools"] = tools

        response = self.client.post(
            f"{self.base_url}/api/chat",
            json=payload
        )
        response.raise_for_status()

        data = response.json()
        message = data.get("message", {})

        # Check for tool calls
        tool_calls = []
        if "tool_calls" in message:
            for tc in message["tool_calls"]:
                func = tc.get("function", {})
                args = func.get("arguments", {})

                # Handle arguments that might be strings
                if isinstance(args, str):
                    try:
                        args = json.loads(args)
                    except json.JSONDecodeError:
                        args = {}

                tool_calls.append(ToolCall(
                    name=func.get("name", ""),
                    arguments=args
                ))

        return ChatResponse(
            content=message.get("content"),
            tool_calls=tool_calls,
            is_tool_call=len(tool_calls) > 0
        )

    def is_available(self) -> bool:
        """Check if Ollama is running."""
        try:
            response = self.client.get(f"{self.base_url}/api/tags")
            return response.status_code == 200
        except:
            return False

    def ensure_model_loaded(self) -> bool:
        """Ensure model is loaded in memory."""
        try:
            response = self.client.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": self.model,
                    "prompt": "hello",
                    "stream": False,
                    "keep_alive": self.keep_alive,
                    "options": {
                        "num_predict": 8,
                        "num_ctx": self.num_ctx
                    }
                }
            )
            return response.status_code == 200
        except Exception as e:
            print(f"Error loading model: {e}")
            return False
