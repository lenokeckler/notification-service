# app/infra/table_client.py
import os
from azure.data.tables import TableServiceClient, UpdateMode

TABLE_NAME = os.getenv("TABLE_NAME", "notifications")
CONN_STR = os.getenv("AZURE_STORAGE_CONNECTION_STRING")


def get_table_client():
    if not CONN_STR:
        raise RuntimeError("AZURE_STORAGE_CONNECTION_STRING no está configurada en .env")

    service = TableServiceClient.from_connection_string(conn_str=CONN_STR)
    return service.get_table_client(table_name=TABLE_NAME)


def insert_notification(entity: dict):
    table_client = get_table_client()
    table_client.create_entity(entity=entity)


def get_user_notifications(user_id: str, top: int = 50):
    """
    Devuelve las notificaciones de un usuario (PartitionKey = user_id).
    Usa query_filter porque tu SDK lo pide así.
    """
    table_client = get_table_client()

    entities = table_client.query_entities(
        query_filter=f"PartitionKey eq '{user_id}'"
    )

    notis = list(entities)
    return notis[:top]


def mark_as_read(user_id: str, row_key: str):
    """
    Marca la notificación como leída.
    OJO: hay que volver a mandar PartitionKey y RowKey en el dict.
    """
    table_client = get_table_client()

    # 1) Traemos la entidad original
    entity = table_client.get_entity(partition_key=user_id, row_key=row_key)

    # 2) Le marcamos read = True
    entity["read"] = True

    # 3) Actualizamos usando el enum correcto
    table_client.update_entity(
        entity=entity,
        mode=UpdateMode.MERGE  # <- ESTE es el cambio importante
    )


def delete_notification(user_id: str, row_key: str):
    table_client = get_table_client()
    table_client.delete_entity(partition_key=user_id, row_key=row_key)
