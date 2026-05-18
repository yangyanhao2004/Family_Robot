from pydantic import BaseModel
from typing import Literal, Optional, Any

class CommandPayload(BaseModel):
    command: Literal["forward", "backward", "left", "right", "stop", "take_photo", "servo1", "servo2", "speed_low", "speed_medium", "speed_high"]
    angle: float | None = None

class CommandMessage(BaseModel):
    type: Literal["command"]
    payload: CommandPayload

# ---- AI Chat ----

class AIChatPayload(BaseModel):
    user_id: int
    message: str

class AIChatMessage(BaseModel):
    type: Literal["ai_chat"]
    payload: AIChatPayload

class AIChatResponsePayload(BaseModel):
    text: str
    action: Literal["chat_reply", "control_robot", "set_reminder"]
    data: Optional[Any] = None

class AIChatResponseMessage(BaseModel):
    type: Literal["ai_chat_response"]
    payload: AIChatResponsePayload

class AISessionEndPayload(BaseModel):
    user_id: int

class AISessionEndMessage(BaseModel):
    type: Literal["ai_session_end"]
    payload: AISessionEndPayload
