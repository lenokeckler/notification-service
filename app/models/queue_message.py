# app/models/queue_message.py
from typing import Any, Optional
from pydantic import BaseModel


class QueueMessage(BaseModel):
    type: str
    userId: str
    data: Optional[Any] = None
