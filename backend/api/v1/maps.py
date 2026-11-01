"""
Endpoints de Mapas de Calor Geoespaciales (/api/v1/maps/heatmap/{farm_id}).

Aplica la Regla de Oro:
- Consultas internas sobre `FincaORM`, `LoteORM` y `DeteccionFitosanitariaORM` en español.
- Contrato HTTP REST (`GET /api/v1/maps/heatmap/{farm_id}`) y estándar RFC 7946 GeoJSON en inglés.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.api.v1.geospatial import obtener_mapa_calor_fitosanitario_lote
from backend.core.database import LoteORM, obtener_sesion_bd
from backend.schemas.api_schemas import RespuestaMapaCalorGeoJSON

router = APIRouter(prefix="/maps", tags=["Mapas de Calor Geoespaciales (GeoJSON / PostGIS)"])


@router.get("/heatmap/{farm_id}", response_model=RespuestaMapaCalorGeoJSON)
def obtener_mapa_calor_por_finca_o_lote(
    farm_id: str, sesion: Session = Depends(obtener_sesion_bd)
):
    """Acepta tanto un identificador de finca (`FINCA-TOL-01`) como de lote (`LOTE-ESPINAL-01`)."""
    lote = (
        sesion.query(LoteORM)
        .filter((LoteORM.id == farm_id) | (LoteORM.finca_id == farm_id))
        .first()
    )
    id_lote_efectivo = lote.id if lote is not None else farm_id
    return obtener_mapa_calor_fitosanitario_lote(lot_id=id_lote_efectivo, sesion=sesion)
