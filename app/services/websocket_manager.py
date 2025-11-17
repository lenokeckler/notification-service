# app/services/websocket_manager.py
from typing import Dict, Set
from fastapi import WebSocket
from datetime import datetime


class WebSocketManager:
    """
    Mantiene las conexiones WebSocket por usuario.
    user_id -> set(WebSocket)
    """
    def __init__(self):
        # Use a more robust data structure
        self.active_connections: Dict[str, Set[WebSocket]] = {}
        self.connection_metadata: Dict[str, dict] = {}

    async def connect(self, user_id: str, websocket: WebSocket):
        await websocket.accept()
        if user_id not in self.active_connections:
            self.active_connections[user_id] = set()
            self.connection_metadata[user_id] = {}

        self.active_connections[user_id].add(websocket)

        # Store connection metadata
        self.connection_metadata[user_id][websocket] = {
            "connected_at": datetime.utcnow().isoformat(),
            "client_ip": websocket.client.host if websocket.client else "unknown"
        }
        print(f"✅ WebSocket connected for user {user_id}")

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
