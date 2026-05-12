from pydantic import BaseModel
from typing import Literal

class CommandPayload(BaseModel):
    command: Literal["forward", "backward", "left", "right", "stop", "light_on", "light_off", "take_photo"]

class CommandMessage(BaseModel):
    type: Literal["command"]
    payload: CommandPayload
