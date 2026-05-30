from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.schemas.message_schema import MessageCreateRequest, MessageOut
from app.services.message_service import create_message, list_messages, serialize_message


router = APIRouter(prefix="/chats/{chat_id}/messages", tags=["messages"])


@router.get("", response_model=list[MessageOut])
def get_messages(
    chat_id: str,
    limit: int = Query(default=50, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[dict]:
    return list_messages(db, current_user, chat_id, limit)


@router.post("", response_model=MessageOut, status_code=status.HTTP_201_CREATED)
def send_message_fallback(
    chat_id: str,
    payload: MessageCreateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    message = create_message(db, current_user, chat_id, payload.type, payload.body)
    return serialize_message(message)

