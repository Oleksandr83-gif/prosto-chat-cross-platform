from collections import defaultdict

from fastapi import WebSocket


class ConnectionManager:
    def __init__(self) -> None:
        self.active_connections: dict[str, list[WebSocket]] = defaultdict(list)

    async def connect(self, chat_id: str, websocket: WebSocket) -> None:
        await websocket.accept()
        self.active_connections[chat_id].append(websocket)

    def disconnect(self, chat_id: str, websocket: WebSocket) -> None:
        connections = self.active_connections.get(chat_id, [])
        if websocket in connections:
            connections.remove(websocket)
        if not connections and chat_id in self.active_connections:
            del self.active_connections[chat_id]

    async def broadcast_json(self, chat_id: str, message: dict) -> None:
        failed: list[WebSocket] = []
        for connection in list(self.active_connections.get(chat_id, [])):
            try:
                await connection.send_json(message)
            except Exception:
                failed.append(connection)

        for connection in failed:
            self.disconnect(chat_id, connection)

