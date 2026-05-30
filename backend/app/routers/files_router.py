from fastapi import APIRouter, Depends, File, UploadFile, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.runtime import amqp_publisher
from app.schemas.file_schema import FileOut
from app.services.file_service import get_file_for_user, list_user_files, save_chat_file, serialize_file


router = APIRouter(tags=["files"])


@router.post("/chats/{chat_id}/files", response_model=FileOut, status_code=status.HTTP_201_CREATED)
async def upload_chat_file(
    chat_id: str,
    upload: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    stored_file = await save_chat_file(db, current_user, chat_id, upload)
    serialized = serialize_file(stored_file)
    amqp_publisher.publish("file.uploaded", serialized)
    return serialized


@router.get("/files", response_model=list[FileOut])
def get_files(
    direction: str = "received",
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[dict]:
    return [serialize_file(file) for file in list_user_files(db, current_user, direction)]


@router.get("/files/{file_id}/download")
def download_file(
    file_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> FileResponse:
    stored_file = get_file_for_user(db, current_user, file_id)
    return FileResponse(
        path=stored_file.storage_path,
        media_type=stored_file.mime_type,
        filename=stored_file.file_name,
    )
