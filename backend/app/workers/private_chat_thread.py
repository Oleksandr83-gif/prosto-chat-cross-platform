from collections.abc import Callable
from queue import Empty, Queue
from threading import Event, Thread
from typing import Any

from sqlalchemy.orm import Session, sessionmaker

from app.amqp.rabbitmq import AMQPPublisher
from app.models.user import User
from app.services.message_service import create_message, serialize_message


BroadcastCallback = Callable[[str, dict[str, Any]], None]


class PrivateChatThread(Thread):
    def __init__(
        self,
        chat_id: str,
        session_factory: sessionmaker[Session],
        publisher: AMQPPublisher,
        broadcast_callback: BroadcastCallback,
    ) -> None:
        super().__init__(name=f"PrivateChatThread-{chat_id}", daemon=True)
        self.chat_id = chat_id
        self.session_factory = session_factory
        self.publisher = publisher
        self.broadcast_callback = broadcast_callback
        self.queue: Queue[dict[str, Any]] = Queue()
        self.stop_event = Event()

    def enqueue(self, message: dict[str, Any]) -> None:
        self.queue.put(message)

    def stop(self) -> None:
        self.stop_event.set()

    def run(self) -> None:
        while not self.stop_event.is_set():
            try:
                message = self.queue.get(timeout=0.5)
            except Empty:
                continue

            try:
                self.process_message(message)
            except Exception as exc:
                print(f"[thread:{self.chat_id}] message processing failed: {exc}")
            finally:
                self.queue.task_done()

    def process_message(self, payload: dict[str, Any]) -> None:
        db = self.session_factory()
        try:
            sender = db.get(User, payload["sender_id"])
            if not sender:
                return

            message = create_message(
                db=db,
                current_user=sender,
                chat_id=self.chat_id,
                message_type=payload.get("type", "text"),
                body=payload.get("body"),
            )
            serialized = serialize_message(message)
            event = {"event": "message.created", "payload": serialized}

            self.publisher.publish("message.created", serialized)
            self.broadcast_callback(self.chat_id, event)
        finally:
            db.close()

