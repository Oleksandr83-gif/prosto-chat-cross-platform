from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.message import Message
from app.models.user import User
from app.services.chat_service import ensure_member


def serialize_message(message: Message) -> dict:
    return {
        "id": message.id,
        "chat_id": message.chat_id,
        "sender_id": message.sender_id,
        "sender_name": message.sender.display_name if message.sender else "Unknown",
        "type": message.type,
        "body": message.body,
        "created_at": message.created_at.isoformat(),
    }


def list_messages(db: Session, current_user: User, chat_id: str, limit: int = 50) -> list[dict]:
    ensure_member(db, chat_id, current_user.id)
    limit = max(1, min(limit, 100))
    messages = db.scalars(
        select(Message)
        .where(Message.chat_id == chat_id, Message.deleted_at.is_(None))
        .order_by(Message.created_at.desc())
        .limit(limit)
    ).all()
    return [serialize_message(message) for message in reversed(messages)]


def create_message(db: Session, current_user: User, chat_id: str, message_type: str, body: str | None) -> Message:
    ensure_member(db, chat_id, current_user.id)
    if message_type == "text" and not body:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Text message body is required")

    message = Message(chat_id=chat_id, sender_id=current_user.id, type=message_type, body=body)
    db.add(message)
    db.commit()
    db.refresh(message)
    return message

