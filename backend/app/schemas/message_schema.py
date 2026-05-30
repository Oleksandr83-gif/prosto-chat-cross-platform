from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class MessageCreateRequest(BaseModel):
    type: str = Field(default="text", pattern="^(text|file|system)$")
    body: str | None = Field(default=None, max_length=5000)


class MessageOut(BaseModel):
    id: str
    chat_id: str
    sender_id: str
    sender_name: str
    type: str
    body: str | None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

