# app/main.py
import os
from dotenv import load_dotenv

# 1) cargar variables de entorno del .env
load_dotenv()

import asyncio
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.notifications import router as notifications_router
from app.api.websocket import router as ws_router
from app.infra.servicebus_consumer import consume_notifications

app = FastAPI(title="Notification Service")

# 2) CORS (puedes limitar orígenes en prod)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 3) Rutas REST
app.include_router(notifications_router)
# 4) Ruta WebSocket
app.include_router(ws_router)


@app.on_event("startup")
async def startup_event():
    # 5) lanzar el consumer de Service Bus en background
    asyncio.create_task(consume_notifications())
