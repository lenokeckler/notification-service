# app/security/jwt_utils.py
import os
import jwt
from fastapi import HTTPException, status

# leemos del .env (tú pusiste hola123)
JWT_SECRET = os.getenv("JWT_SECRET", "hola123")
JWT_ALG = os.getenv("JWT_ALG", "HS256")


def decode_token(token: str) -> dict:
    """
    Decodifica y valida el JWT (para WebSocket u otros).
    Lanza 401 si es inválido.
    """
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALG])
        return payload
    except jwt.PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido",
        )


def get_current_user(authorization_header: str) -> dict:
    """
    Toma el header: Authorization: Bearer <token>
    Lo valida y devuelve el payload.
    Lanza 401 si falta o es inválido.
    """
    if not authorization_header:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing Authorization header",
        )

    if not authorization_header.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Authorization header format",
        )

    token = authorization_header.removeprefix("Bearer ").strip()

    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALG])
    except jwt.PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
        )

    if "sub" not in payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token without subject",
        )

    return payload
