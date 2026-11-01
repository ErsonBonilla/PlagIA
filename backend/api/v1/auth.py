"""
Endpoints de Autenticación Empresarial JWT (/api/v1/auth).

Aplica la Regla de Oro:
- Funciones, variables y mensajes de error internos en español.
- Rutas REST y esquemas del contrato JSON (`access_token`, `token_type`) en inglés.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status

from backend.core.security import (
    autenticar_usuario,
    crear_token_acceso,
    obtener_usuario_actual_opcional,
)
from backend.schemas.api_schemas import RespuestaToken, SolicitudToken

router = APIRouter(prefix="/auth", tags=["Seguridad y Roles"])


@router.post("/login", response_model=RespuestaToken)
@router.post("/token", response_model=RespuestaToken)
def iniciar_sesion_para_token(carga: SolicitudToken):
    usuario = autenticar_usuario(carga.username, carga.password)
    if usuario is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales inválidas. Verifique su usuario y contraseña corporativa.",
        )
    token = crear_token_acceso(
        sujeto=usuario["usuario"],
        rol=usuario["rol"],
        distrito=usuario["distrito"],
    )
    return RespuestaToken(
        access_token=token,
        role=usuario["rol"],
        district=usuario["distrito"],
        full_name=usuario["nombre_completo"],
    )


@router.get("/me")
def obtener_perfil_operador_actual(usuario: dict = Depends(obtener_usuario_actual_opcional)):
    return usuario
