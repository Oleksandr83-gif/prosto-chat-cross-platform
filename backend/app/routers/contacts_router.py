from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user
from app.models.contact import Contact
from app.models.user import User
from app.schemas.contact_schema import ContactCreateRequest, ContactOut
from app.services.contact_service import add_contact, delete_contact, list_contacts


router = APIRouter(prefix="/contacts", tags=["contacts"])


@router.get("", response_model=list[ContactOut])
def get_contacts(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> list[Contact]:
    return list_contacts(db, current_user.id)


@router.post("", response_model=ContactOut, status_code=status.HTTP_201_CREATED)
def create_contact(
    payload: ContactCreateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Contact:
    return add_contact(db, current_user, payload.user_number)


@router.delete("/{contact_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_contact(
    contact_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Response:
    delete_contact(db, current_user, contact_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)

