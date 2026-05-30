import re
from pathlib import Path
from uuid import uuid4

from fastapi import HTTPException, UploadFile, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import settings
from app.models.chat_member import ChatMember
from app.models.file import StoredFile
from app.models.message import Message
from app.models.user import User
from app.services.chat_service import ensure_member


def _safe_filename(filename: str) -> str:
    name = Path(filename).name or "file"
    return re.sub(r"[^A-Za-z0-9._-]+", "_", name)


def serialize_file(file: StoredFile) -> dict:
    return {
        "id": file.id,
        "chat_id": file.chat_id,
        "message_id": file.message_id,
        "sender_id": file.sender_id,
        "file_name": file.file_name,
        "mime_type": file.mime_type,
        "size_bytes": file.size_bytes,
        "url": f"/media/uploads/{Path(file.storage_path).name}",
        "created_at": file.created_at,
    }


async def save_chat_file(db: Session, current_user: User, chat_id: str, upload: UploadFile) -> StoredFile:
    ensure_member(db, chat_id, current_user.id)
    settings.media_dir.mkdir(parents=True, exist_ok=True)

    original_name = _safe_filename(upload.filename or "uploaded-file")
    storage_name = f"{uuid4()}_{original_name}"
    storage_path = settings.media_dir / storage_name

    size = 0
    with storage_path.open("wb") as target:
        while chunk := await upload.read(1024 * 1024):
            size += len(chunk)
            target.write(chunk)

    message = Message(chat_id=chat_id, sender_id=current_user.id, type="file", body=original_name)
    db.add(message)
    db.flush()

    stored_file = StoredFile(
        chat_id=chat_id,
        message_id=message.id,
        sender_id=current_user.id,
        file_name=original_name,
        mime_type=upload.content_type,
        size_bytes=size,
        storage_path=str(storage_path),
    )
    db.add(stored_file)
    db.commit()
    db.refresh(stored_file)
    return stored_file


def list_user_files(db: Session, current_user: User, direction: str) -> list[StoredFile]:
    if direction not in {"sent", "received"}:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="direction must be sent or received")

    query = (
        select(StoredFile)
        .join(ChatMember, StoredFile.chat_id == ChatMember.chat_id)
        .where(ChatMember.user_id == current_user.id, ChatMember.is_hidden.is_(False))
        .order_by(StoredFile.created_at.desc())
    )

    if direction == "sent":
        query = query.where(StoredFile.sender_id == current_user.id)
    else:
        query = query.where(StoredFile.sender_id != current_user.id)

    return list(db.scalars(query))


def get_file_for_user(db: Session, current_user: User, file_id: str) -> StoredFile:
    stored_file = db.get(StoredFile, file_id)
    if not stored_file:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not found")

    ensure_member(db, stored_file.chat_id, current_user.id)
    if not Path(stored_file.storage_path).exists():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Stored file is missing")
    return stored_file

