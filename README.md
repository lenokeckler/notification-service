# Servicio de Notificaciones

Un servicio de notificaciones en tiempo real construido con FastAPI que se integra con Azure Service Bus y Azure Table Storage. Este servicio proporciona APIs REST y conexiones WebSocket para gestionar y entregar notificaciones a los usuarios.

## Arquitectura

```
notification-service/
├── app/
│   ├── api/              # Endpoints REST y WebSocket
│   │   ├── notifications.py
│   │   └── websocket.py
│   ├── infra/            # Clientes de infraestructura Azure
│   │   ├── servicebus_consumer.py
│   │   └── table_client.py
│   ├── models/           # Modelos de datos Pydantic
│   │   ├── notification.py
│   │   └── queue_message.py
│   ├── security/         # Autenticación JWT
│   │   └── jwt_utils.py
│   ├── services/         # Lógica de negocio
│   │   ├── notification_handler.py
│   │   └── websocket_manager.py
│   └── main.py           # Aplicación FastAPI
├── certs/                # Certificados mTLS (opcional)
└── .github/
    └── workflows/        # Pipeline CI/CD
```

## ✨ Características

- **Notificaciones en Tiempo Real**: Conexiones WebSocket para entrega instantánea de notificaciones
- **API REST**: Operaciones CRUD completas para gestión de notificaciones
- **Integración con Azure Service Bus**: Procesamiento asíncrono de mensajes desde cola
- **Azure Table Storage**: Almacenamiento persistente de notificaciones
- **Autenticación JWT**: Autenticación y autorización segura de usuarios
- **Soporte mTLS**: TLS mutuo opcional para entornos de producción
- **Soporte CORS**: Intercambio de recursos de origen cruzado configurable

## Inicio Rápido

### Prerequisitos

- Python 3.9+
- Cuenta de Azure con:
  - Namespace de Service Bus y cola
  - Cuenta de Storage con Table Storage
- Clave secreta JWT

### Instalación

1. Clonar el repositorio:

```bash
git clone <url-del-repositorio>
cd notification-service
```

2. Crear un entorno virtual:

```bash
python -m venv .venv
.venv\Scripts\activate
```

3. Instalar dependencias:

```bash
pip install -r requirements.txt
```

4. Configurar variables de entorno (crear archivo `.env`):

```env
# Azure Service Bus
AZURE_SERVICE_BUS_CONNECTION_STRING=tu_cadena_conexion_servicebus
AZURE_SERVICE_BUS_QUEUE_NAME=notifications-queue

# Azure Table Storage
AZURE_STORAGE_CONNECTION_STRING=tu_cadena_conexion_storage
AZURE_TABLE_NAME=notifications

# Configuración JWT
JWT_SECRET_KEY=tu_clave_secreta_aqui
JWT_ALGORITHM=HS256

# Opcional: Configuración mTLS
MTLS_ENABLED=false
CERT_FILE=certs/server.crt
KEY_FILE=certs/server.key
CA_FILE=certs/ca.crt

# Configuración CORS
CORS_ORIGINS=http://localhost:3000,https://dominio.com
```

5. Ejecutar la aplicación:

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## Endpoints de la API

### Verificación de Salud

```http
GET /health
```

### Notificaciones

#### Obtener notificaciones del usuario

```http
GET /api/notifications
Authorization: Bearer {jwt_token}
```

Parámetros de consulta:

- `skip`: Número de registros a omitir (predeterminado: 0)
- `limit`: Número máximo de registros a devolver (predeterminado: 100)

#### Marcar notificación como leída

```http
PUT /api/notifications/{notification_id}/read
Authorization: Bearer {jwt_token}
```

#### Eliminar notificación

```http
DELETE /api/notifications/{notification_id}
Authorization: Bearer {jwt_token}
```

### WebSocket

#### Notificaciones en tiempo real

```
WS /ws?token={jwt_token}
```

Conectarse para recibir notificaciones en tiempo real del usuario autenticado.

## Autenticación

El servicio utiliza tokens JWT para autenticación. Incluir el token en:

- **API REST**: Encabezado `Authorization: Bearer {token}`
- **WebSocket**: Parámetro de consulta `token`

Ejemplo de payload del token:

```json
{
  "sub": "user123",
  "exp": 1700000000
}
```

##  Flujo de Notificaciones

1. **El mensaje llega** a la cola de Azure Service Bus
2. **El consumidor de Service Bus** procesa el mensaje
3. **El manejador de notificaciones** crea la notificación en Table Storage
4. **El gestor de WebSocket** envía la notificación a usuarios conectados en tiempo real
5. **Los usuarios** pueden consultar, marcar como leídas o eliminar notificaciones mediante la API REST

## Formato de Mensajes

### Mensaje de Cola Service Bus

```json
{
  "userId": "user123",
  "type": "info",
  "message": "Tu pedido ha sido enviado",
  "metadata": {
    "orderId": "12345",
    "trackingNumber": "ABC123"
  }
}
```

### Modelo de Notificación

```json
{
  "id": "uuid-v4",
  "userId": "user123",
  "type": "info",
  "message": "Tu pedido ha sido enviado",
  "metadata": {
    "orderId": "12345"
  },
  "isRead": false,
  "createdAt": "2025-11-17T10:30:00Z"
}
```

##  Pruebas

Ejecutar pruebas con pytest:

```bash
pytest
```

## Despliegue

### Docker

```bash
docker build -t notification-service .
docker run -p 8000:8000 --env-file .env notification-service
```

### Azure Container Apps

El repositorio incluye workflow de GitHub Actions para despliegue automatizado a Azure Container Apps.

Secretos requeridos:

- `AZURE_CREDENTIALS`
- `AZURE_SERVICE_BUS_CONNECTION_STRING`
- `AZURE_STORAGE_CONNECTION_STRING`
- `JWT_SECRET_KEY`

## Variables de Entorno

| Variable                              | Requerida | Descripción                                      |
| ------------------------------------- | --------- | ------------------------------------------------ |
| `AZURE_SERVICE_BUS_CONNECTION_STRING` | Sí        | Cadena de conexión de Azure Service Bus          |
| `AZURE_SERVICE_BUS_QUEUE_NAME`        | Sí        | Nombre de la cola de Service Bus                 |
| `AZURE_STORAGE_CONNECTION_STRING`     | Sí        | Cadena de conexión de Azure Storage              |
| `AZURE_TABLE_NAME`                    | Sí        | Nombre de la tabla de Azure                      |
| `JWT_SECRET_KEY`                      | Sí        | Clave secreta para validación de tokens JWT      |
| `JWT_ALGORITHM`                       | No        | Algoritmo JWT (predeterminado: HS256)            |
| `MTLS_ENABLED`                        | No        | Habilitar mTLS (predeterminado: false)           |
| `CERT_FILE`                           | No        | Ruta al certificado SSL                          |
| `KEY_FILE`                            | No        | Ruta a la clave privada SSL                      |
| `CA_FILE`                             | No        | Ruta al certificado CA                           |
| `CORS_ORIGINS`                        | No        | Lista de orígenes permitidos separados por comas |

## 🛠️ Tecnologías

- **FastAPI**: Framework web moderno para construir APIs
- **Uvicorn**: Servidor ASGI
- **Azure Service Bus**: Cola de mensajes para procesamiento asíncrono
- **Azure Table Storage**: Almacenamiento NoSQL para notificaciones
- **PyJWT**: Manejo de tokens JWT
- **Pydantic**: Validación de datos
- **WebSockets**: Comunicación en tiempo real