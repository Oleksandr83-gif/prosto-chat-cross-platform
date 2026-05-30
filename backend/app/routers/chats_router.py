from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.schemas.chat_schema import (
    ChatMemberAddRequest,
    ChatOut,
    GroupChatCreateRequest,
    PrivateChatCreateRequest,
)
from app.services.chat_service import (
    add_group_member,
    create_group_chat,
    create_private_chat,
    get_chat_for_user,
    hide_chat_for_user,
    list_chats,
    remove_group_member,
)


router = APIRouter(prefix="/chats", tags=["chats"])


@router.get("", response_model=list[ChatOut])
def get_chats(
    type: str | None = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[ChatOut]:
    return list_chats(db, current_user, type)


@router.get("/{chat_id}", response_model=ChatOut)
def get_chat(chat_id: str, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> ChatOut:
    return get_chat_for_user(db, chat_id, current_user)


@router.post("/private", response_model=ChatOut, status_code=status.HTTP_201_CREATED)
def create_private(
    payload: PrivateChatCreateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ChatOut:
    return create_private_chat(db, current_user, payload.contact_user_id)


@router.post("/group", response_model=ChatOut, status_code=status.HTTP_201_CREATED)
def create_group(
    payload: GroupChatCreateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ChatOut:
    return create_group_chat(db, current_user, payload.name, payload.member_ids)


@router.delete("/{chat_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_chat(
    chat_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Response:
    hide_chat_for_user(db, current_user, chat_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/{chat_id}/members", response_model=ChatOut)
def add_member(
    chat_id: str,
    payload: ChatMemberAddRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ChatOut:
    return add_group_member(db, current_user, chat_id, payload.user_id)


@router.delete("/{chat_id}/members/{user_id}", response_model=ChatOut)
def remove_member(
    chat_id: str,
    user_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ChatOut:
    return remove_group_member(db, current_user, chat_id, user_id)

