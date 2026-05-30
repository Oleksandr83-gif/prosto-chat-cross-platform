from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.user_schema import UserPublic


class ChatMemberOut(BaseModel):
    user: UserPublic
    role: str
    is_hidden: bool
    joined_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ChatOut(BaseModel):
    id: str
    type: str
    name: str | None = None
    title: str
    owner_user_id: str | None = None
    created_at: datetime
    members: list[ChatMemberOut]

    model_config = ConfigDict(from_attributes=True)


class PrivateChatCreateRequest(BaseModel):
    contact_user_id: str


class GroupChatCreateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=160)
    member_ids: list[str] = Field(default_factory=list)


class ChatMemberAddRequest(BaseModel):
    user_id: str

