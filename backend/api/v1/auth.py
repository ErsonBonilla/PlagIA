"""
Endpoints de Autenticación Empresarial JWT (/api/v1/auth).
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status

from backend.core.security import (
    authenticate_user,
    create_access_token,
    get_optional_current_user,
)
from backend.schemas.api_schemas import TokenRequest, TokenResponse

router = APIRouter(prefix="/auth", tags=["Seguridad y Roles"])


@router.post("/token", response_model=TokenResponse)
def login_for_access_token(payload: TokenRequest):
    user = authenticate_user(payload.username, payload.password)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales inválidas. Verifique usuario y contraseña corporativa.",
        )
    token = create_access_token(
        subject=user["username"],
        role=user["role"],
        district=user["district"],
    )
    return TokenResponse(
        access_token=token,
        role=user["role"],
        district=user["district"],
        full_name=user["full_name"],
    )


@router.get("/me")
def get_current_operator_profile(user: dict = Depends(get_optional_current_user)):
    return user
