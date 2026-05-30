from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.schemas.user_schema import UserPublic


class ContactCreateRequest(BaseModel):
    user_number: str


class ContactOut(BaseModel):
    id: str
    owner_user_id: str
    contact_user_id: str
    created_at: datetime
    contact_user: UserPublic

    model_config = ConfigDict(from_attributes=True)

