from datetime import datetime, timedelta, timezone
from random import randint

import bcrypt
from fastapi import HTTPException, status
from jose import JWTError, jwt
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.config import settings
from app.models.privacy_settings import PrivacySettings
from app.models.user import User
from app.schemas.auth_schema import LoginRequest, RegisterRequest


def verify_password(plain_password: str, password_hash: str) -> bool:
    return bcrypt.checkpw(plain_password.encode("utf-8")[:72], password_hash.encode("utf-8"))


def get_password_hash(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8")[:72], bcrypt.gensalt()).decode("utf-8")


def create_access_token(user_id: str) -> str:
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=settings.jwt_expire_minutes)
    payload = {"sub": user_id, "exp": expires_at}
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def decode_access_token(token: str) -> str:
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
        user_id = payload.get("sub")
    except JWTError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token") from exc

    if not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token payload")
    return str(user_id)


def generate_user_number(db: Session) -> str:
    for _ in range(1000):
        candidate = f"PC-{randint(100, 999)}-{randint(100, 999)}"
        exists = db.scalar(select(User).where(User.user_number == candidate))
        if not exists:
            return candidate
    raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Could not generate user number")


def register_user(db: Session, payload: RegisterRequest) -> User:
    if not payload.email and not payload.phone:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email or phone is required")

    filters = []
    if payload.email:
        filters.append(User.email == payload.email)
    if payload.phone:
        filters.append(User.phone == payload.phone)

    if filters and db.scalar(select(User).where(or_(*filters))):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="User with this email or phone already exists")

    user = User(
        user_number=generate_user_number(db),
        display_name=payload.display_name,
        email=str(payload.email) if payload.email else None,
        phone=payload.phone,
        password_hash=get_password_hash(payload.password),
        avatar_url=payload.avatar_url,
        age=payload.age,
        status="online",
    )
    db.add(user)
    db.flush()

    db.add(PrivacySettings(user_id=user.id))
    db.commit()
    db.refresh(user)
    return user


def authenticate_user(db: Session, payload: LoginRequest) -> User:
    user = db.scalar(
        select(User).where(
            or_(
                User.email == payload.login,
                User.phone == payload.login,
                User.display_name == payload.login,
                User.user_number == payload.login,
            )
        )
    )
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid login or password")

    user.status = "online"
    db.commit()
    db.refresh(user)
    return user
