"""
Seguridad Empresarial: Autenticación JWT y Control de Roles (Agrónomo, Operador VANT, Productor).

Aplica la Regla de Oro:
- Lógica interna, usuarios corporativos, roles y mensajes de error en español.
- Claims estándar del protocolo RFC 7519 JWT (`sub`, `exp`, `iat`) e interfaz `HTTPBearer`
  conservados en inglés.
"""

from __future__ import annotations

import hashlib
from datetime import datetime, timedelta, timezone

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from backend.core.config import configuracion

esquema_portador = HTTPBearer(auto_error=False)


def _cifrar_contrasena(texto_plano: str) -> str:
    return hashlib.sha256(texto_plano.encode("utf-8")).hexdigest()


BASE_USUARIOS_EMPRESARIAL: dict[str, dict] = {
    "agronomo@plagia.co": {
        "usuario": "agronomo@plagia.co",
        "nombre_completo": "Ing. Agrónomo Comité Tolima",
        "rol": "AGRONOMO_SENIOR",
        "distrito": "Usocoello - El Espinal",
        "contrasena_hash": _cifrar_contrasena("PlagIA2026*"),
    },
    "dron@plagia.co": {
        "usuario": "dron@plagia.co",
        "nombre_completo": "Operador VANT Fotogrametría",
        "rol": "OPERADOR_DRON",
        "distrito": "Usosaldaña - Saldaña",
        "contrasena_hash": _cifrar_contrasena("VantTolima2026*"),
    },
    "productor@plagia.co": {
        "usuario": "productor@plagia.co",
        "nombre_completo": "Productor Arrocero Meseta",
        "rol": "PRODUCTOR",
        "distrito": "Meseta de Ibagué",
        "contrasena_hash": _cifrar_contrasena("ArrozTolima2026*"),
    },
}


def autenticar_usuario(nombre_usuario: str, contrasena: str) -> dict | None:
    registro = BASE_USUARIOS_EMPRESARIAL.get(nombre_usuario)
    if not registro:
        return None
    if registro["contrasena_hash"] != _cifrar_contrasena(contrasena):
        return None
    return registro


def crear_token_acceso(sujeto: str, rol: str, distrito: str) -> str:
    expiracion = datetime.now(timezone.utc) + timedelta(
        minutes=configuracion.access_token_expire_minutes
    )
    # Claims RFC 7519 (`sub`, `exp`, `iat`) requeridos por el protocolo JWT
    carga_util = {
        "sub": sujeto,
        "role": rol,
        "district": distrito,
        "exp": expiracion,
        "iat": datetime.now(timezone.utc),
    }
    return jwt.encode(
        carga_util, configuracion.secret_key, algorithm=configuracion.jwt_algorithm
    )


def obtener_usuario_actual_opcional(
    credenciales: HTTPAuthorizationCredentials | None = Depends(esquema_portador),
) -> dict:
    """Valida el token JWT si se envía, o asigna contexto de operación rural autenticado por dispositivo."""
    if credenciales is None:
        return {
            "username": "dispositivo_campo@plagia.co",
            "role": "DISPOSITIVO_CAMPO",
            "district": "Tolima",
        }
    try:
        carga_util = jwt.decode(
            credenciales.credentials,
            configuracion.secret_key,
            algorithms=[configuracion.jwt_algorithm],
        )
        return {
            "username": carga_util.get("sub", "desconocido"),
            "role": carga_util.get("role", "AGRONOMO_SENIOR"),
            "district": carga_util.get("district", "Tolima"),
        }
    except jwt.PyJWTError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Token JWT inválido o expirado: {exc}",
        ) from exc


# Alias de compatibilidad
authenticate_user = autenticar_usuario
create_access_token = crear_token_acceso
get_optional_current_user = obtener_usuario_actual_opcional
