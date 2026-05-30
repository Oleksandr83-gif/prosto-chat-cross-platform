from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.chat import Chat
from app.models.chat_member import ChatMember
from app.models.user import User
from app.schemas.chat_schema import ChatOut


def ensure_member(db: Session, chat_id: str, user_id: str) -> ChatMember:
    member = db.scalar(
        select(ChatMember).where(
            ChatMember.chat_id == chat_id,
            ChatMember.user_id == user_id,
            ChatMember.is_hidden.is_(False),
        )
    )
    if not member:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User is not a chat member")
    return member


def ensure_admin(db: Session, chat_id: str, user_id: str) -> ChatMember:
    member = ensure_member(db, chat_id, user_id)
    if member.role not in {"owner", "admin"}:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin role is required")
    return member


def serialize_chat(chat: Chat, current_user_id: str) -> ChatOut:
    title = chat.name or "Chat"
    if chat.type == "private":
        other = next((member.user for member in chat.members if member.user_id != current_user_id), None)
        title = other.display_name if other else "Private chat"

    return ChatOut(
        id=chat.id,
        type=chat.type,
        name=chat.name,
        title=title,
        owner_user_id=chat.owner_user_id,
        created_at=chat.created_at,
        members=list(chat.members),
    )


def list_chats(db: Session, current_user: User, chat_type: str | None = None) -> list[ChatOut]:
    query = (
        select(Chat)
        .join(ChatMember)
        .where(ChatMember.user_id == current_user.id, ChatMember.is_hidden.is_(False))
        .order_by(Chat.created_at.desc())
    )
    if chat_type:
        query = query.where(Chat.type == chat_type)

    chats = db.scalars(query).unique().all()
    return [serialize_chat(chat, current_user.id) for chat in chats]


def get_chat_for_user(db: Session, chat_id: str, current_user: User) -> ChatOut:
    ensure_member(db, chat_id, current_user.id)
    chat = db.get(Chat, chat_id)
    if not chat:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Chat not found")
    return serialize_chat(chat, current_user.id)


def _find_existing_private_chat(db: Session, user_a_id: str, user_b_id: str) -> Chat | None:
    user_chats = db.scalars(
        select(Chat)
        .join(ChatMember)
        .where(Chat.type == "private", ChatMember.user_id == user_a_id)
    ).unique()

    for chat in user_chats:
        member_ids = {member.user_id for member in chat.members}
        if member_ids == {user_a_id, user_b_id}:
            return chat
    return None


def _get_chat_member(db: Session, chat_id: str, user_id: str) -> ChatMember | None:
    return db.scalar(select(ChatMember).where(ChatMember.chat_id == chat_id, ChatMember.user_id == user_id))


def _ensure_private_member(db: Session, chat_id: str, user_id: str) -> ChatMember:
    member = _get_chat_member(db, chat_id, user_id)
    if member:
        return member

    member = ChatMember(chat_id=chat_id, user_id=user_id, role="member")
    db.add(member)
    return member


def restore_chat_visibility_for_members(db: Session, chat_id: str) -> None:
    chat = db.get(Chat, chat_id)
    if not chat or chat.type not in {"private", "group"}:
        return

    # Нове повідомлення має повернути чат у список усіх учасників, доданих у цей діалог.
    for member in chat.members:
        if member.is_hidden:
            member.is_hidden = False


def create_private_chat(db: Session, current_user: User, contact_user_id: str) -> ChatOut:
    contact_user = db.get(User, contact_user_id)
    if not contact_user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contact user not found")
    if contact_user.id == current_user.id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Private chat with yourself is not allowed")

    existing = _find_existing_private_chat(db, current_user.id, contact_user.id)
    if existing:
        _ensure_private_member(db, existing.id, current_user.id)
        _ensure_private_member(db, existing.id, contact_user.id)
        restore_chat_visibility_for_members(db, existing.id)
        db.commit()
        db.refresh(existing)
        return serialize_chat(existing, current_user.id)

    chat = Chat(type="private")
    db.add(chat)
    db.flush()
    db.add_all(
        [
            ChatMember(chat_id=chat.id, user_id=current_user.id, role="member"),
            ChatMember(chat_id=chat.id, user_id=contact_user.id, role="member"),
        ]
    )
    db.commit()
    db.refresh(chat)
    return serialize_chat(chat, current_user.id)


def create_group_chat(db: Session, current_user: User, name: str, member_ids: list[str]) -> ChatOut:
    chat = Chat(type="group", name=name, owner_user_id=current_user.id)
    db.add(chat)
    db.flush()

    db.add(ChatMember(chat_id=chat.id, user_id=current_user.id, role="owner"))
    unique_member_ids = {member_id for member_id in member_ids if member_id != current_user.id}
    for member_id in unique_member_ids:
        if not db.get(User, member_id):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"User {member_id} not found")
        db.add(ChatMember(chat_id=chat.id, user_id=member_id, role="member"))

    db.commit()
    db.refresh(chat)
    return serialize_chat(chat, current_user.id)


def hide_chat_for_user(db: Session, current_user: User, chat_id: str) -> None:
    member = ensure_member(db, chat_id, current_user.id)
    member.is_hidden = True
    db.commit()


def add_group_member(db: Session, current_user: User, chat_id: str, user_id: str) -> ChatOut:
    ensure_admin(db, chat_id, current_user.id)
    chat = db.get(Chat, chat_id)
    if not chat or chat.type != "group":
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Group chat not found")
    if not db.get(User, user_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    if db.scalar(select(ChatMember).where(ChatMember.chat_id == chat_id, ChatMember.user_id == user_id)):
        return serialize_chat(chat, current_user.id)

    db.add(ChatMember(chat_id=chat_id, user_id=user_id, role="member"))
    db.commit()
    db.refresh(chat)
    return serialize_chat(chat, current_user.id)


def remove_group_member(db: Session, current_user: User, chat_id: str, user_id: str) -> ChatOut:
    ensure_admin(db, chat_id, current_user.id)
    chat = db.get(Chat, chat_id)
    if not chat or chat.type != "group":
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Group chat not found")
    if user_id == chat.owner_user_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Owner cannot be removed")

    member = db.scalar(select(ChatMember).where(ChatMember.chat_id == chat_id, ChatMember.user_id == user_id))
    if not member:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Member not found")
    db.delete(member)
    db.commit()
    db.refresh(chat)
    return serialize_chat(chat, current_user.id)
