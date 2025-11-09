# app/api/websocket.py
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query
from app.security.jwt_utils import decode_token
from app.services.websocket_manager import ws_manager

router = APIRouter(tags=["websocket"])


@router.websocket("/ws/notifications")
async def websocket_notifications(websocket: WebSocket, token: str = Query(...)):
    """
    WebSocket para notificaciones en tiempo real.
    El frontend debe conectarse con:
      ws://localhost:8001/ws/notifications?token=JWT_AQUI
    """
    # 1. Validar token
    payload = decode_token(token)
    user_id = payload.get("sub")
    if not user_id:
        # no tiene sub -> no sabemos quién es
        await websocket.close()
        return

    # 2. Registrar conexión
    await ws_manager.connect(user_id, websocket)

    try:
        # 3. Mantener la conexión viva
        while True:
            # si quieres recibir algo del cliente:
            await websocket.receive_text()
            # o puedes hacer ping-pong aquí
    except WebSocketDisconnect:
        ws_manager.disconnect(user_id, websocket)
