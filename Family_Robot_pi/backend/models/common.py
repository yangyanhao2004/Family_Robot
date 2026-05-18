from pydantic import BaseModel
from typing import Literal, Optional

class BaseMessage(BaseModel):
    type: str

class RegisterMessage(BaseModel):
    type: Literal["register"]
    role: Literal["web", "robot"]
    user_id: Optional[int] = None

class ErrorMessage(BaseModel):
    type: Literal["error"]
    message: str
