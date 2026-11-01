"""
Endpoints de Carga de Ortomosaicos Aéreos de Drones (/api/v1/drones/upload).

Aplica la Regla de Oro:
- Lógica interna, modelos ORM y mensajes descriptivos en español.
- Contrato HTTP REST (`POST /api/v1/drones/upload`) conservado en inglés.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, File, Form, UploadFile
from sqlalchemy.orm import Session

from backend.api.v1.inference import enviar_ortomosaico_dron
from backend.core.database import obtener_sesion_bd
from backend.schemas.api_schemas import RespuestaTrabajoOrtomosaico

router = APIRouter(prefix="/drones", tags=["Fotogrametría VANT y Ortomosaicos"])


@router.post("/upload", response_model=RespuestaTrabajoOrtomosaico)
async def cargar_ortomosaico_dron(
    file: UploadFile = File(..., description="Ortomosaico GeoTIFF de alta resolución (VANT)"),
    lot_id: str = Form(default="LOTE-ESPINAL-01"),
    sesion: Session = Depends(obtener_sesion_bd),
):
    return await enviar_ortomosaico_dron(file=file, lot_id=lot_id, sesion=sesion)
