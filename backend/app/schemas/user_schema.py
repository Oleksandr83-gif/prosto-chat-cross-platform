from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr


class UserPublic(BaseModel):
    id: str
    user_number: str
    display_name: str
    email: EmailStr | None = None
    phone: str | None = None
    avatar_url: str | None = None
    age: int | None = None
    status: str
    created_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)


class UserUpdateRequest(BaseModel):
    display_name: str | None = None
    email: EmailStr | None = None
    phone: str | None = None
    avatar_url: str | None = None
    age: int | None = None


class UserSearchResponse(BaseModel):
    id: str
    user_number: str
    display_name: str
    status: str
    email: EmailStr | None = None
    phone: str | None = None
    age: int | None = None

