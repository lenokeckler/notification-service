# app/main.py
import os
import ssl
from dotenv import load_dotenv

# 1) cargar variables de entorno del .env
load_dotenv()

import asyncio
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from app.api.notifications import router as notifications_router
from app.api.websocket import router as ws_router
from app.infra.servicebus_consumer import consume_notifications

app = FastAPI(title="Notification Service")

# === Certificate Thumbprints for mTLS validation ===
ALLOWED_THUMBPRINTS = [
    '1F:2D:94:4C:C9:D8:6C:8E:B2:09:F2:AA:80:F5:22:2F:67:68:A9:15:34:1A:77:D7:13:18:88:A6:33:FE:F7:73'
]

# === mTLS Certificate Validation Middleware ===
@app.middleware("http")
async def validate_client_certificate(request: Request, call_next):
    # Skip validation in development mode
    if os.getenv("NODE_ENV") == "development" or os.getenv("SKIP_MTLS") == "true":
        request.state.client_cert_verified = False
        return await call_next(request)
    
    # Get peer certificate
    cert = request.scope.get("client")
    if not cert or not hasattr(cert, "peercert"):
        raise HTTPException(status_code=401, detail="Client certificate required")
    
    # Extract thumbprint
    # Implementation depends on your ASGI server (uvicorn with SSL)
    # For Azure App Service, certificate is in headers
    client_cert = request.headers.get("X-ARR-ClientCert")
    if not client_cert:
        raise HTTPException(status_code=401, detail="No client certificate")
    
    # Validate thumbprint matches APIM
    if os.getenv("APIM_THUMBPRINT") not in client_cert:
        raise HTTPException(status_code=403, detail="Invalid client certificate")
    
    return await call_next(request)

# 2) CORS (puedes limitar orígenes en prod)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[os.getenv("CORS_ORIGIN", "http://localhost:3000")],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 3) Rutas REST
app.include_router(notifications_router)
# 4) Ruta WebSocket
app.include_router(ws_router)


@app.get("/")
async def root():
    return {
        "service": "Notification Service",
        "status": "running",
        "timestamp": "2025-11-17T00:00:00.000Z"
    }


@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "database": "connected",  # TODO: Add actual database health check
        "timestamp": "2025-11-17T00:00:00.000Z"
    }


@app.get("/debug/consumer-status")
async def consumer_status():
    # TODO: Add actual consumer status check
    return {"status": "running"}


@app.on_event("startup")
async def startup_event():
    # 5) lanzar el consumer de Service Bus en background
    asyncio.create_task(consume_notifications())


def create_ssl_context():
    """Create SSL context for HTTPS with mTLS"""
    if os.getenv("NODE_ENV") == "development" or os.getenv("SKIP_MTLS") == "true":
        return None

    try:
        ssl_context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
        ssl_context.load_cert_chain(
            certfile="certs/server-cert.pem",
            keyfile="certs/server-key.pem"
        )
        ssl_context.load_verify_locations("certs/ca-cert.pem")
        ssl_context.verify_mode = ssl.CERT_REQUIRED
        return ssl_context
    except Exception as e:
        print(f"⚠️ SSL context creation failed: {e}")
        print("💡 Falling back to HTTP mode")
        return None


if __name__ == "__main__":
    port = int(os.getenv("PORT", 8001))
    host = os.getenv("HOST", "0.0.0.0")

    ssl_context = create_ssl_context()

    if ssl_context:
        print(f"🚀 Notification Service (HTTPS mTLS) running on https://{host}:{port}")
        print("✅ Certificate validation enabled")
    else:
        print(f"🚀 Notification Service (HTTP) running on http://{host}:{port}")
        print("⚠️ mTLS validation skipped - set SKIP_MTLS=false to enable")

    uvicorn.run(
        "app.main:app",
        host=host,
        port=port,
        reload=os.getenv("NODE_ENV") == "development",
        ssl_keyfile="certs/server-key.pem" if ssl_context else None,
        ssl_certfile="certs/server-cert.pem" if ssl_context else None,
        ssl_ca_certs="certs/ca-cert.pem" if ssl_context else None,
        ssl_cert_reqs="required" if ssl_context else None,
    )
