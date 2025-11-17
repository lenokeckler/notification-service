# app/services/websocket_manager.py
from typing import Dict, Set
from fastapi import WebSocket


class WebSocketManager:
    """
    Mantiene las conexiones WebSocket por usuario.
    user_id -> set(WebSocket)
    """
    def __init__(self):
        self.active_connections: Dict[str, Set[WebSocket]] = {}

    async def connect(self, user_id: str, websocket: WebSocket):
        await websocket.accept()
        if user_id not in self.active_connections:
            self.active_connections[user_id] = set()
        self.active_connections[user_id].add(websocket)

    def disconnect(self, user_id: str, websocket: WebSocket):
        if user_id in self.active_connections:
            self.active_connections[user_id].discard(websocket)
            if not self.active_connections[user_id]:
                del self.active_connections[user_id]

    async def send_to_user(self, user_id: str, message: dict):
        """
        Envía un mensaje a TODAS las conexiones de ese usuario
        (tabs distintas, dispositivos, etc.)
        """
        if user_id not in self.active_connections:
            return
        dead_sockets = []
        for ws in self.active_connections[user_id]:
            try:
                await ws.send_json(message)
            except Exception:
                dead_sockets.append(ws)
        # limpiar sockets muertos
        for ws in dead_sockets:
            self.active_connections[user_id].discard(ws)

    async def broadcast(self, message: dict):
        for user_id in list(self.active_connections.keys()):
            await self.send_to_user(user_id, message)


# instancia global
ws_manager = WebSocketManager()
