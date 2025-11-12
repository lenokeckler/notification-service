# app/infra/servicebus_consumer.py
import os
import json
import asyncio

from azure.servicebus.aio import ServiceBusClient
from azure.servicebus import TransportType

from app.services.notification_handler import process_notification

# ====== env ======
SB_CONN_STR = os.getenv("AZURE_SERVICE_BUS_CONNECTION_STRING")
SB_QUEUE = os.getenv("AZURE_SERVICE_BUS_QUEUE_NAME", "notifications-queue")


async def consume_notifications():
    """
    Consumer asíncrono de Azure Service Bus:
      - AMQP sobre WebSocket (443) para funcionar en App Service.
      - Lee mensajes de la cola y llama process_notification(payload).
      - Confirma (complete) sólo si procesó OK.
      - Reconecta con backoff si se cae.
    """
    if not SB_CONN_STR:
        print("⚠️  Falta AZURE_SERVICE_BUS_CONNECTION_STRING. No se consumirá la cola.")
        return

    if not SB_QUEUE:
        print("⚠️  Falta AZURE_SERVICE_BUS_QUEUE_NAME. No se consumirá la cola.")
        return

    backoff = 5  # segundos (puedes incrementar gradualmente si quieres)

    while True:
        try:
            print(f"[consumer] ⚙️ Conectando a Service Bus (cola: {SB_QUEUE}) con WebSockets 443…")
            async with ServiceBusClient.from_connection_string(
                SB_CONN_STR,
                transport_type=TransportType.AmqpOverWebsocket,  # clave para 443
            ) as sb_client:
                receiver = sb_client.get_queue_receiver(
                    queue_name=SB_QUEUE,
                    max_wait_time=20,  # espera lote
                )
                async with receiver:
                    print(f"[consumer] ✅ Escuchando cola: {SB_QUEUE}")
                    while True:
                        # recibe lote
                        messages = await receiver.receive_messages(
                            max_message_count=10,
                            max_wait_time=10,
                        )
                        if not messages:
                            await asyncio.sleep(0.5)
                            continue

                        for msg in messages:
                            try:
                                # >>> OJO: leer bytes del body <<<
                                body_bytes = b"".join(part for part in msg.body)
                                payload = json.loads(body_bytes.decode("utf-8"))

                                print("[consumer] 📥 Mensaje recibido:", payload)

                                # Persistir + WS
                                await process_notification(payload)

                                # Confirmar
                                await receiver.complete_message(msg)
                                print("[consumer] ✅ Mensaje completado")
                            except Exception as e:
                                # No completar => reintenta (o DLQ por MaxDeliveryCount)
                                print("[consumer] ❗ Error procesando mensaje:", e)

            # si sale del with sin error, pequeña pausa antes de reconectar
            await asyncio.sleep(1)

        except Exception as e:
            print(f"[consumer] 🔁 Error de conexión, reintento en {backoff}s ->", e)
            await asyncio.sleep(backoff)
            # opcional: backoff = min(30, backoff * 2)

