from pydantic import BaseModel, Field
from typing import Literal, Optional

MessageType = Literal["join", "leave", "msg", "ping"]

class ClientMessage(BaseModel):
    id: Optional[str] = None
    type: MessageType
    room: Optional[str] = Field(default="chat")
    text: Optional[str] = None

class ServerMessage(BaseModel):
    id: Optional[str] = None
    type: str
    room: Optional[str] = None
    text: Optional[str] = None
    ts: int
