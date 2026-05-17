from pydantic import BaseModel
from typing import Literal

class CommandPayload(BaseModel):
    command: Literal["forward", "backward", "left", "right", "stop", "take_photo", "servo1", "servo2", "speed_low", "speed_medium", "speed_high"]
    angle: float | None = None

class CommandMessage(BaseModel):
    type: Literal["command"]
    payload: CommandPayload
