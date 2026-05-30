from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.schemas.privacy_schema import PrivacyOut, PrivacyUpdateRequest
from app.schemas.user_schema import UserPublic, UserSearchResponse, UserUpdateRequest
from app.services.user_service import (
    get_privacy_settings,
    search_user_by_number,
    update_privacy_settings,
    update_user_profile,
)


router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me", response_model=UserPublic)
def me(current_user: User = Depends(get_current_user)) -> User:
    return current_user


@router.patch("/me", response_model=UserPublic)
def update_me(
    payload: UserUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> User:
    return update_user_profile(db, current_user, payload)


@router.get("/search", response_model=UserSearchResponse)
def search_user(user_number: str, db: Session = Depends(get_db)) -> UserSearchResponse:
    return search_user_by_number(db, user_number)


@router.get("/me/privacy", response_model=PrivacyOut)
def privacy(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return get_privacy_settings(db, current_user)


@router.patch("/me/privacy", response_model=PrivacyOut)
def update_privacy(
    payload: PrivacyUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return update_privacy_settings(db, current_user, payload)

