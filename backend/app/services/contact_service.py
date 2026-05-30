from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.contact import Contact
from app.models.user import User


def list_contacts(db: Session, owner_user_id: str) -> list[Contact]:
    return list(db.scalars(select(Contact).where(Contact.owner_user_id == owner_user_id).order_by(Contact.created_at.desc())))


def add_contact(db: Session, owner: User, user_number: str) -> Contact:
    contact_user = db.scalar(select(User).where(User.user_number == user_number))
    if not contact_user or (contact_user.privacy_settings and not contact_user.privacy_settings.allow_search):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    if contact_user.id == owner.id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="You cannot add yourself to contacts")

    existing = db.scalar(
        select(Contact).where(Contact.owner_user_id == owner.id, Contact.contact_user_id == contact_user.id)
    )
    if existing:
        return existing

    contact = Contact(owner_user_id=owner.id, contact_user_id=contact_user.id)
    db.add(contact)
    db.commit()
    db.refresh(contact)
    return contact


def delete_contact(db: Session, owner: User, contact_id: str) -> None:
    contact = db.scalar(select(Contact).where(Contact.id == contact_id, Contact.owner_user_id == owner.id))
    if not contact:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contact not found")
    db.delete(contact)
    db.commit()

