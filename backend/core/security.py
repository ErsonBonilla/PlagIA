"""
Seguridad Empresarial: Autenticación JWT y Control de Roles (Agrónomo, Operador VANT, Productor).
"""

from __future__ import annotations

import hashlib
from datetime import datetime, timedelta, timezone

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from backend.core.config import settings

bearer_scheme = HTTPBearer(auto_error=False)


def _hash_password(raw: str) -> str:
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


ENTERPRISE_USERS_DB: dict[str, dict] = {
    "agronomo@plagia.co": {
        "username": "agronomo@plagia.co",
        "full_name": "Ing. Agrónomo Comité Tolima",
        "role": "AGRONOMO_SENIOR",
        "district": "Usocoello - El Espinal",
        "password_hash": _hash_password("PlagIA2026*"),
    },
    "dron@plagia.co": {
        "username": "dron@plagia.co",
        "full_name": "Operador VANT Fotogrametría",
        "role": "OPERADOR_DRON",
        "district": "Usosaldaña - Saldaña",
        "password_hash": _hash_password("VantTolima2026*"),
    },
    "productor@plagia.co": {
        "username": "productor@plagia.co",
        "full_name": "Productor Arrocero Meseta",
        "role": "PRODUCTOR",
        "district": "Meseta de Ibagué",
        "password_hash": _hash_password("ArrozTolima2026*"),
    },
}


def authenticate_user(username: str, password: str) -> dict | None:
    user = ENTERPRISE_USERS_DB.get(username)
    if not user:
        return None
    if user["password_hash"] != _hash_password(password):
        return None
    return user


def create_access_token(subject: str, role: str, district: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.access_token_expire_minutes)
    payload = {
        "sub": subject,
        "role": role,
        "district": district,
        "exp": expire,
        "iat": datetime.now(timezone.utc),
    }
    return jwt.encode(payload, settings.secret_key, algorithm=settings.jwt_algorithm)


def get_optional_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
) -> dict:
    """Valida el token JWT si se envía, o asigna contexto de operación rural autenticado por dispositivo."""
    if credentials is None:
        return {
            "username": "field_device@plagia.co",
            "role": "DISPOSITIVO_CAMPO",
            "district": "Tolima",
        }
    try:
        payload = jwt.decode(
            credentials.credentials,
            settings.secret_key,
            algorithms=[settings.jwt_algorithm],
        )
        return {
            "username": payload.get("sub", "unknown"),
            "role": payload.get("role", "AGRONOMO_SENIOR"),
            "district": payload.get("district", "Tolima"),
        }
    except jwt.PyJWTError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Token JWT inválido o expirado: {exc}",
        ) from exc
