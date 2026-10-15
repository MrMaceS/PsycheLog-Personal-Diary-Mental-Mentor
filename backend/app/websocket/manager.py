from typing import Dict, List
from fastapi import WebSocket, WebSocketDisconnect
from app.core.logging_config import get_logger

logger = get_logger(__name__)


class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[int, List[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, user_id: int):
        """Принимает новое WebSocket-соединение."""
        await websocket.accept()
        if user_id not in self.active_connections:
            self.active_connections[user_id] = []
        self.active_connections[user_id].append(websocket)
        logger.info("websocket_connected", user_id=user_id)

    def disconnect(self, websocket: WebSocket, user_id: int):
        """Разрывает соединение."""
        if user_id in self.active_connections:
            self.active_connections[user_id].remove(websocket)
            if not self.active_connections[user_id]:
                del self.active_connections[user_id]
            logger.info("websocket_disconnected", user_id=user_id)

    async def send_personal_message(self, message: dict, user_id: int):
        """Отправляет сообщение конкретному пользователю (по всем его устройствам)."""
        if user_id in self.active_connections:
            for connection in self.active_connections[user_id]:
                await connection.send_json(message)

    async def broadcast_to_chat(self, message: dict, member_user_ids: List[int]):
        """Рассылает сообщение всем участникам чата."""
        for user_id in member_user_ids:
            await self.send_personal_message(message, user_id)


manager = ConnectionManager()