"""
In-memory session manager for multi-turn conversations.

Sessions are NOT persisted to DB.
- Web sessions: created on first ai_chat, destroyed on logout/disconnect.
- Pi sessions: created on startup, destroyed on shutdown.
"""

import threading
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional

tz = timezone(timedelta(hours=8))


@dataclass
class ChatSession:
    session_id: str
    user_id: int
    messages: List[Dict[str, str]] = field(default_factory=list)
    created_at: datetime = field(default_factory=lambda: datetime.now(tz))
    last_active: datetime = field(default_factory=lambda: datetime.now(tz))

    MAX_TURNS = 10  # Kept small to stay within Moonshot Tier0 TPM limits (500K/min)

    def add_message(self, role: str, content: str):
        self.messages.append({"role": role, "content": content})
        self.last_active = datetime.now(tz)
        while len(self.messages) > self.MAX_TURNS:
            self.messages.pop(0)

    def get_messages(self) -> List[Dict[str, str]]:
        return list(self.messages)


class SessionManager:
    """Thread-safe singleton managing per-user chat sessions."""

    def __init__(self):
        self._sessions: Dict[int, ChatSession] = {}
        self._lock = threading.Lock()

    def get_or_create(self, user_id: int) -> ChatSession:
        with self._lock:
            if user_id not in self._sessions:
                self._sessions[user_id] = ChatSession(
                    session_id=f"web-{user_id}",
                    user_id=user_id
                )
            return self._sessions[user_id]

    def get(self, user_id: int) -> Optional[ChatSession]:
        with self._lock:
            return self._sessions.get(user_id)

    def destroy(self, user_id: int):
        with self._lock:
            self._sessions.pop(user_id, None)

    def is_active(self, user_id: int) -> bool:
        with self._lock:
            return user_id in self._sessions


session_manager = SessionManager()
