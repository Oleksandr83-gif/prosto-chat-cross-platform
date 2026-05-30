from collections.abc import Generator
from time import sleep

from sqlalchemy import create_engine
from sqlalchemy.exc import OperationalError
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
