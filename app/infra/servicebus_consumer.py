# app/infra/servicebus_consumer.py
import os
import json
import asyncio
from datetime import datetime, timezone

from azure.servicebus.aio import ServiceBusClient
from azure.servicebus import TransportType

from app.services.notification_handler import process_notification

SB_CONN_STR = os.getenv("AZURE_SERVICE_BUS_CONNECTION_STRING")
SB_QUEUE = os.getenv("AZURE_SERVICE_BUS_QUEUE_NAME", "notifications-queue")

# ➕ ESTADO para diagnóstico
CONSUMER_STARTED_AT = None
LAST_SB_MSG_AT = None
LAST_ERROR = None

def _utcnow_iso():
    return datetime.now(timezone.utc).isoformat()

async def consume_notifications():
    """Consume mensajes reales desde Azure Service Bus (AMQP over WebSockets)."""
    global CONSUMER_STARTED_AT, LAST_SB_MSG_AT, LAST_ERROR

    if not SB_CONN_STR:
        print("⚠️  Service Bus no configurado. No se consumirá la cola.")
        LAST_ERROR = "SB_CONN_STR missing"
        return

    CONSUMER_STARTED_AT = _utcnow_iso()
    LAST_ERROR = None
    print(f"✅ Conectando a Service Bus (cola: {SB_QUEUE}) usando WebSockets...")

    servicebus_client = ServiceBusClient.from_connection_string(
        conn_str=SB_CONN_STR,
        transport_type=TransportType.AmqpOverWebsocket,
    )

    async with servicebus_client:
        receiver = servicebus_client.get_queue_receiver(queue_name=SB_QUEUE)
        async with receiver:
            while True:
                try:
                    messages = await receiver.receive_messages(
                        max_message_count=5,
                        max_wait_time=5,
                    )
                    if not messages:
                        await asyncio.sleep(1)
                        continue

                    for msg in messages:
                        try:
                            body = str(msg)
                            data = json.loads(body)
                            print("📩 Mensaje recibido de SB:", data)

                            await process_notification(data)
                            await receiver.complete_message(msg)

                            LAST_SB_MSG_AT = _utcnow_iso()
                            LAST_ERROR = None
                        except Exception as e:
                            LAST_ERROR = f"process_error: {e}"
                            print("❌ Error procesando mensaje:", e)
                except Exception as e:
                    LAST_ERROR = f"receive_error: {e}"
                    print("⚠️  Error recibiendo de Service Bus, reintentando en 3s...", e)
                    await asyncio.sleep(3)

def consumer_status():
    """Devuelve un snapshot del estado del consumer."""
    return {
        "queue": SB_QUEUE,
        "startedAt": CONSUMER_STARTED_AT,
        "lastMessageAt": LAST_SB_MSG_AT,
        "lastError": LAST_ERROR,
        "hasConnectionString": bool(SB_CONN_STR),
    }
