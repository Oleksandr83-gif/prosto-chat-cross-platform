import asyncio
from typing import Any

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.database import SessionLocal
from app.models.chat import Chat
from app.models.user import User
from app.runtime import amqp_publisher, connection_manager, thread_manager
from app.services.auth_service import decode_access_token
from app.services.chat_service import ensure_member
from app.services.message_service import create_message, serialize_message


router = APIRouter(tags=["websocket"])


def _broadcast_scheduler(loop: asyncio.AbstractEventLoop):
    def schedule(chat_id: str, event: dict[str, Any]) -> None:
        asyncio.run_coroutine_threadsafe(connection_manager.broadcast_json(chat_id, event), loop)

    return schedule


@router.websocket("/ws/chats/{chat_id}")
async def chat_websocket(websocket: WebSocket, chat_id: str, token: str | None = None) -> None:
    if not token:
        await websocket.close(code=1008)
        return

    db = SessionLocal()
    loop = asyncio.get_running_loop()
    schedule_broadcast = _broadcast_scheduler(loop)

    try:
        user_id = decode_access_token(token)
        current_user = db.get(User, user_id)
        chat = db.get(Chat, chat_id)

        if not current_user or not chat:
            await websocket.close(code=1008)
            return

        ensure_member(db, chat_id, current_user.id)
        await connection_manager.connect(chat_id, websocket)

        if chat.type == "private":
            thread_manager.start_private_chat_thread(chat_id, schedule_broadcast)

        amqp_publisher.publish("user.online", {"user_id": current_user.id, "chat_id": chat_id})

        while True:
            data = await websocket.receive_json()
            event_name = data.get("event")

            if event_name == "message.send":
                payload = data.get("payload") or {}
                message_type = payload.get("type", "text")
                body = payload.get("body")

                if chat.type == "private":
                    thread_manager.send_message_to_thread(
                        chat_id,
                        {"sender_id": current_user.id, "type": message_type, "body": body},
                        schedule_broadcast,
                    )
                else:
                    message = create_message(db, current_user, chat_id, message_type, body)
                    serialized = serialize_message(message)
                    amqp_publisher.publish("message.created", serialized)
                    await connection_manager.broadcast_json(chat_id, {"event": "message.created", "payload": serialized})

            elif event_name in {"typing.start", "typing.stop", "message.read"}:
                await connection_manager.broadcast_json(
                    chat_id,
                    {
                        "event": event_name,
                        "chat_id": chat_id,
                        "sender_id": current_user.id,
                        "payload": data.get("payload") or {},
                    },
                )

    except WebSocketDisconnect:
        connection_manager.disconnect(chat_id, websocket)
        if "current_user" in locals():
            amqp_publisher.publish("user.offline", {"user_id": current_user.id, "chat_id": chat_id})
    finally:
        connection_manager.disconnect(chat_id, websocket)
        db.close()

