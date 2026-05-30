from collections.abc import Callable
from threading import Lock
from typing import Any

from sqlalchemy.orm import Session, sessionmaker

from app.amqp.rabbitmq import AMQPPublisher
from app.workers.private_chat_thread import PrivateChatThread


BroadcastCallback = Callable[[str, dict[str, Any]], None]


class ThreadManager:
    def __init__(self, session_factory: sessionmaker[Session], publisher: AMQPPublisher) -> None:
        self.session_factory = session_factory
        self.publisher = publisher
        self.active_threads: dict[str, PrivateChatThread] = {}
        self.lock = Lock()

    def start_private_chat_thread(self, chat_id: str, broadcast_callback: BroadcastCallback) -> PrivateChatThread:
        with self.lock:
            thread = self.active_threads.get(chat_id)
            if thread and thread.is_alive():
                thread.broadcast_callback = broadcast_callback
                return thread

            thread = PrivateChatThread(chat_id, self.session_factory, self.publisher, broadcast_callback)
            self.active_threads[chat_id] = thread
            thread.start()
            print(f"[threads] started private chat thread: {chat_id}")
            return thread

    def send_message_to_thread(
        self,
        chat_id: str,
        message: dict[str, Any],
        broadcast_callback: BroadcastCallback,
    ) -> None:
        thread = self.start_private_chat_thread(chat_id, broadcast_callback)
        thread.enqueue(message)

    def stop_private_chat_thread(self, chat_id: str) -> None:
        with self.lock:
            thread = self.active_threads.pop(chat_id, None)
            if thread:
                thread.stop()

    def stop_all(self) -> None:
        with self.lock:
            threads = list(self.active_threads.values())
            self.active_threads.clear()

        for thread in threads:
            thread.stop()

