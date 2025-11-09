# app/models/notification.py
from typing import Any, Optional
from pydantic import BaseModel


class Notification(BaseModel):
    PartitionKey: str      # userId
    RowKey: str            # id único
    type: str
    title: str
    message: str
    read: bool = False
    createdAt: str
    data: Optional[Any] = None
