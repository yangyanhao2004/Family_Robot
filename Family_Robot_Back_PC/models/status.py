from pydantic import BaseModel
from typing import Literal

class StatusPayload(BaseModel):
    battery: int
    isRunning: bool
    temperature: float
    signalStrength: int

class StatusMessage(BaseModel):
    type: Literal["status"]
    payload: StatusPayload
