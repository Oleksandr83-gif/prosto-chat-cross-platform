from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.privacy_settings import PrivacySettings
from app.models.user import User
from app.schemas.privacy_schema import PrivacyUpdateRequest
from app.schemas.user_schema import UserSearchResponse, UserUpdateRequest


def update_user_profile(db: Session, user: User, payload: UserUpdateRequest) -> User:
    data = payload.model_dump(exclude_unset=True)
    for field, value in data.items():
        setattr(user, field, value)
    db.commit()
    db.refresh(user)
    return user


def get_privacy_settings(db: Session, user: User) -> PrivacySettings:
    settings = user.privacy_settings
    if not settings:
        settings = PrivacySettings(user_id=user.id)
        db.add(settings)
        db.commit()
        db.refresh(settings)
    return settings


def update_privacy_settings(db: Session, user: User, payload: PrivacyUpdateRequest) -> PrivacySettings:
    settings = get_privacy_settings(db, user)
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(settings, field, value)
    db.commit()
    db.refresh(settings)
    return settings


def search_user_by_number(db: Session, user_number: str) -> UserSearchResponse:
    user = db.scalar(select(User).where(User.user_number == user_number))
    if not user or (user.privacy_settings and not user.privacy_settings.allow_search):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    privacy = user.privacy_settings
    return UserSearchResponse(
        id=user.id,
        user_number=user.user_number,
        display_name=user.display_name,
        status=user.status,
        email=user.email if privacy and privacy.show_email else None,
        phone=user.phone if privacy and privacy.show_phone else None,
        age=user.age if privacy and privacy.show_age else None,
    )

