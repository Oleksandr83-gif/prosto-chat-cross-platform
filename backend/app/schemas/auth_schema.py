from pydantic import BaseModel, EmailStr, Field

from app.schemas.user_schema import UserPublic


class RegisterRequest(BaseModel):
    display_name: str = Field(min_length=2, max_length=120)
    email: EmailStr | None = None
    phone: str | None = None
    password: str = Field(min_length=6, max_length=128)
    age: int | None = Field(default=None, ge=0, le=130)
    avatar_url: str | None = None


class LoginRequest(BaseModel):
    login: str = Field(min_length=1)
    password: str = Field(min_length=1)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserPublic

