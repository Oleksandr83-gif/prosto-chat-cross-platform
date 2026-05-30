from datetime import datetime

from pydantic import BaseModel, ConfigDict


class FileOut(BaseModel):
    id: str
    chat_id: str
    message_id: str | None
    sender_id: str
    file_name: str
    mime_type: str | None
    size_bytes: int | None
    url: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

