from pydantic import BaseModel
from typing import Literal

class BaseMessage(BaseModel):
    type: str

class RegisterMessage(BaseModel):
    type: Literal["register"]
    role: Literal["web", "robot"]

class ErrorMessage(BaseModel):
    type: Literal["error"]
    message: str
