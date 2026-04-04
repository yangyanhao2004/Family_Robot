from pydantic import BaseModel
from typing import Literal, Optional, Dict, Any

class WebRTCSignalingData(BaseModel):
    type: Literal["offer", "answer", "candidate"]
    offer: Optional[Dict[str, Any]] = None
    answer: Optional[Dict[str, Any]] = None
    candidate: Optional[Dict[str, Any]] = None

class WebRTCSignalingMessage(BaseModel):
    type: Literal["webrtc_signaling"]
    data: WebRTCSignalingData
