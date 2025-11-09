# app/infra/servicebus_consumer.py
import os
import json
import asyncio

from azure.servicebus.aio import ServiceBusClient
from azure.servicebus import TransportType  # versión 7.x usa este nombre

from app.services.notification_handler import process_notification

# ====== env ======
SB_CONN_STR = os.getenv("AZURE_SERVICE_BUS_CONNECTION_STRING")
SB_QUEUE = os.getenv("AZURE_SERVICE_BUS_QUEUE_NAME", "notifications-queue")


async def consume_notifications():
    """
    Lee mensajes reales de Azure Service Bus (cola).
    Forzamos AMQP over WebSockets para evitar WinError 10054.
    """
    if not SB_CONN_STR:
        print("⚠️  Service Bus no configurado. No se consumirá la cola.")
        return

    # 👇 forzamos WebSocket (puerto 443)
    servicebus_client = ServiceBusClient.from_connection_string(
        conn_str=SB_CONN_STR,
        transport_type=TransportType.AmqpOverWebsocket,
    )

    print(f"✅ Conectando a Service Bus (cola: {SB_QUEUE}) usando WebSockets...")

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

                            # procesar → guarda en Table + WS
                            await process_notification(data)

                            # confirmar a la cola
                            await receiver.complete_message(msg)
                        except Exception as e:
                            print("❌ Error procesando mensaje:", e)
                except Exception as e:
                    # aquí caerá si Azure vuelve a botarte
                    print("⚠️  Error recibiendo de Service Bus, reintentando en 3s...", e)
                    await asyncio.sleep(3)
