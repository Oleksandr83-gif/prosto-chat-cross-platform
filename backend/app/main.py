from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.config import settings
from app.database import init_db_with_retry
from app.routers import auth_router, chats_router, contacts_router, files_router, messages_router, users_router, websocket_router
from app.runtime import thread_manager


def create_app() -> FastAPI:
    app = FastAPI(title=settings.app_name)

    # Налаштовуємо CORS для роботи frontend, REST API та WebSocket з одного домену або локальних портів.
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    settings.media_dir.mkdir(parents=True, exist_ok=True)
    app.mount("/media", StaticFiles(directory=settings.media_dir.parent), name="media")

    @app.on_event("startup")
    def on_startup() -> None:
        # Створюємо схему БД і чекаємо PostgreSQL, якщо контейнер ще підіймається.
        init_db_with_retry()

    @app.on_event("shutdown")
    def on_shutdown() -> None:
        # Закриваємо серверні потоки приватних чатів перед завершенням процесу.
        thread_manager.stop_all()

    @app.get("/health", tags=["system"])
    def health() -> dict[str, str]:
        return {"status": "ok", "service": settings.app_name}

    app.include_router(auth_router.router, prefix=settings.api_prefix)
    app.include_router(users_router.router, prefix=settings.api_prefix)
    app.include_router(contacts_router.router, prefix=settings.api_prefix)
    app.include_router(chats_router.router, prefix=settings.api_prefix)
    app.include_router(messages_router.router, prefix=settings.api_prefix)
    app.include_router(files_router.router, prefix=settings.api_prefix)
    app.include_router(websocket_router.router)

    return app


app = create_app()
