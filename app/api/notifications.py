# app/api/notifications.py
from fastapi import APIRouter, Request, HTTPException, status
from pydantic import BaseModel
from typing import Optional, Dict, Any

from app.security.jwt_utils import get_current_user
from app.infra.table_client import (
    insert_notification,   # reservado por si luego expones un POST real
    get_user_notifications,
    mark_as_read,
)
from app.services.notification_handler import process_notification
from app.infra.servicebus_consumer import consumer_status  # 🔍 diagnóstico consumer

router = APIRouter(prefix="/notifications", tags=["notifications"])


@router.get("/user/{user_id}")
async def list_user_notifications(user_id: str, request: Request):
    """
    Devuelve las notificaciones de un usuario.
    Solo puede ver sus propias notificaciones (comparando sub del JWT).
    """
    auth_header = request.headers.get("Authorization", "")
    current = get_current_user(auth_header)
    if current["sub"] != user_id:
        raise HTTPException(status_code=403, detail="Forbidden")

    notis = get_user_notifications(user_id)
    return notis


@router.get("/unread-count/{user_id}")
async def unread_count(user_id: str, request: Request):
    """
    Cuenta las notificaciones NO leídas de un usuario.
    Si una notificación no trae 'read', se cuenta como NO leída.
    """
    auth_header = request.headers.get("Authorization", "")
    current = get_current_user(auth_header)
    if current["sub"] != user_id:
        raise HTTPException(status_code=403, detail="Forbidden")

    notis = get_user_notifications(user_id)

    unread = 0
    for n in notis:
        is_read = n.get("read", False)
        if not is_read:
            unread += 1

    return {"count": unread}


@router.post("/mark-read/{notification_id}")
async def mark_notification_as_read(notification_id: str, request: Request):
    """
    Marca una notificación como leída.
    Usa el user_id (sub) del JWT y el RowKey de la notificación.
    """
    auth_header = request.headers.get("Authorization", "")
    current = get_current_user(auth_header)
    user_id = current["sub"]

    try:
        mark_as_read(user_id, notification_id)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"No se pudo marcar como leída: {e}",
        )

    return {"ok": True}


@router.post("/test")
async def create_test_notification(request: Request):
    """
    Endpoint de PRUEBA para crear una notificación falsa
    y ver el flujo completo (persistencia + WS).
    Usa el usuario del JWT.
    """
    auth_header = request.headers.get("Authorization", "")
    current = get_current_user(auth_header)
    user_id = current["sub"]

    fake_msg = {
        "type": "WORD_SAVED",
        "userId": user_id,
        "data": {"word": "hola"},
    }

    await process_notification(fake_msg)
    return {"ok": True}


# =========================
# 🔧 DEV-ONLY: /notifications/dev-send
# Enviar una notificación arbitraria (persistencia + WS) para pruebas.
# Requiere JWT; si no se envía userId en el body, usa el del token (sub).
# =========================

class DevSendIn(BaseModel):
    type: str
    userId: Optional[str] = None
    title: Optional[str] = None
    message: Optional[str] = None
    data: Optional[Dict[str, Any]] = None


@router.post("/dev-send")
async def dev_send(body: DevSendIn, request: Request):
    """
    Envía una notificación arbitraria para el usuario indicado
    (o el del JWT si no se manda userId). Útil para probar
    NEW_MESSAGE, WORD_UPDATED, WORD_FORGOTTEN, etc.
    """
    auth_header = request.headers.get("Authorization", "")
    current = get_current_user(auth_header)
    target_user = body.userId or current["sub"]

    msg = {
        "type": body.type,
        "userId": target_user,
        "title": body.title or "",
        "message": body.message or "",
        "data": body.data or {},
    }

    await process_notification(msg)
    return {"ok": True, "echo": msg}


# =========================
# 🔎 Diagnóstico del consumer de Service Bus
# =========================
@router.get("/debug/consumer-status")
async def debug_consumer_status():
    """
    Devuelve el estado del consumer de Service Bus:
    - startedAt: cuándo arrancó
    - lastMessageAt: último mensaje procesado
    - lastError: último error visto (si hubo)
    - queue: nombre de la cola
    - hasConnectionString: si hay conn string configurado
    """
    return consumer_status()
