# app/services/notification_handler.py
from datetime import datetime
import uuid
import json  # <-- importante

from app.infra.table_client import insert_notification
from app.services.websocket_manager import ws_manager


async def process_notification(msg: dict):
    """
    Procesa un mensaje de notificación que viene de la cola.
    Estructura esperada:
      {
        "type": "WORD_SAVED",
        "userId": "123",
        "data": { ... }   # puede venir dict
      }
    """
    user_id = msg.get("userId")
    noti_type = msg.get("type", "GENERIC")
    data = msg.get("data", {})

    if not user_id:
        # si no hay user no hay a quién notificar
        return

    # mapear tipos a textos
    if noti_type == "WORD_SAVED":
        title = "Palabra guardada"
        message = "Se guardó una nueva palabra en tu diccionario."
    elif noti_type == "NEW_MESSAGE":
        title = "Nuevo mensaje"
        message = "Tienes un nuevo mensaje."
    else:
        title = "Notificación"
        message = "Tienes una nueva notificación."

    row_key = str(uuid.uuid4())
    created_at = datetime.utcnow().isoformat()

    # 👇 Azure Table NO acepta dicts directos.
    # Si 'data' es dict, lo pasamos a JSON.
    if isinstance(data, dict):
        data_to_store = json.dumps(data)
    else:
        data_to_store = data

    # 1. Persistir en Table Storage
    entity = {
        "PartitionKey": user_id,
        "RowKey": row_key,
        "type": noti_type,
        "title": title,
        "message": message,
        "read": False,
        "createdAt": created_at,
        "data": data_to_store,   # <- ya es string
    }
    insert_notification(entity)

    # 2. Enviar por WebSocket (si está conectado) → aquí sí podemos mandar el dict
    await ws_manager.send_to_user(user_id, {
        "id": row_key,
        "type": noti_type,
        "title": title,
        "message": message,
        "createdAt": created_at,
        "data": data,   # <- aquí dejamos el dict original
    })
