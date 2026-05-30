from collections.abc import Generator
from random import randint
from time import sleep

from sqlalchemy import create_engine, inspect, text
from sqlalchemy.exc import OperationalError, SQLAlchemyError
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.config import settings


class Base(DeclarativeBase):
    pass


connect_args = {"check_same_thread": False} if settings.database_url.startswith("sqlite") else {}

engine = create_engine(settings.database_url, connect_args=connect_args, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    from app import models  # noqa: F401

    Base.metadata.create_all(bind=engine)
    ensure_chat_room_numbers()


def _generate_existing_room_number(connection, chat_type: str) -> str:
    prefix = "GR" if chat_type == "group" else "PR"
    for _ in range(1000):
        candidate = f"{prefix}-{randint(100, 999)}-{randint(100, 999)}"
        exists = connection.execute(
            text("SELECT 1 FROM chats WHERE room_number = :room_number"),
            {"room_number": candidate},
        ).first()
        if not exists:
            return candidate
    raise RuntimeError("Could not generate chat room number")


def ensure_chat_room_numbers() -> None:
    inspector = inspect(engine)
    if "chats" not in inspector.get_table_names():
        return

    columns = {column["name"] for column in inspector.get_columns("chats")}
    with engine.begin() as connection:
        if "room_number" not in columns:
            connection.execute(text("ALTER TABLE chats ADD COLUMN room_number VARCHAR(32)"))

        rows = connection.execute(text("SELECT id, type FROM chats WHERE room_number IS NULL OR room_number = ''")).mappings().all()
        for row in rows:
            # Старі чати отримують номер кімнати, щоб frontend показував однаковий ідентифікатор для всіх учасників.
            connection.execute(
                text("UPDATE chats SET room_number = :room_number WHERE id = :chat_id"),
                {"room_number": _generate_existing_room_number(connection, row["type"]), "chat_id": row["id"]},
            )

        try:
            connection.execute(text("CREATE UNIQUE INDEX IF NOT EXISTS ix_chats_room_number ON chats (room_number)"))
        except SQLAlchemyError as exc:
            print(f"[db] could not create chat room number index: {exc}")


def init_db_with_retry() -> None:
    last_error: Exception | None = None
    for attempt in range(1, settings.database_startup_retries + 1):
        try:
            init_db()
            return
        except OperationalError as exc:
            last_error = exc
            print(f"[db] waiting for database ({attempt}/{settings.database_startup_retries}): {exc}")
            sleep(settings.database_startup_retry_seconds)

    if last_error:
        raise last_error
