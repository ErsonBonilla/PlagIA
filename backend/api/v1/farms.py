"""
Endpoints de Gestión de Fincas y Lotes Arroceros en el Tolima (/api/v1/farms).

Aplica la Regla de Oro:
- Modelos ORM (`FincaORM`, `LoteORM`), funciones y atributos de tabla en español.
- Contrato JSON de respuesta REST conservado en inglés.
"""

from __future__ import annotations

import json

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.core.database import FincaORM, LoteORM, obtener_sesion_bd
from backend.schemas.api_schemas import EsquemaResumenLote

router = APIRouter(prefix="/farms", tags=["Fincas y Lotes Arroceros (Tolima)"])


@router.get("")
def listar_fincas(sesion: Session = Depends(obtener_sesion_bd)):
    fincas = sesion.query(FincaORM).all()
    return [
        {
            "id": f.id,
            "name": f.nombre,
            "municipality": f.municipio,
            "irrigation_district": f.distrito_riego,
            "owner_name": f.propietario,
            "total_area_ha": f.area_total_ha,
        }
        for f in fincas
    ]


@router.get("/lots", response_model=list[EsquemaResumenLote])
def listar_lotes(sesion: Session = Depends(obtener_sesion_bd)):
    lotes = sesion.query(LoteORM).all()
    return [
        EsquemaResumenLote(
            id=lote.id,
            farm_id=lote.finca_id,
            name=lote.nombre,
            municipality=lote.municipio,
            rice_variety=lote.variedad_arroz,
            crop_age_days=lote.edad_cultivo_dias,
            area_ha=lote.area_ha,
            center_lat=lote.latitud_centro,
            center_lon=lote.longitud_centro,
            polygon_geojson=json.loads(lote.poligono_geojson),
        )
        for lote in lotes
    ]


@router.get("/lots/{lot_id}", response_model=EsquemaResumenLote)
def obtener_detalle_lote(lot_id: str, sesion: Session = Depends(obtener_sesion_bd)):
    lote = sesion.query(LoteORM).filter(LoteORM.id == lot_id).first()
    if lote is None:
        raise HTTPException(status_code=404, detail=f"No existe el lote '{lot_id}'")
    return EsquemaResumenLote(
        id=lote.id,
        farm_id=lote.finca_id,
        name=lote.nombre,
        municipality=lote.municipio,
        rice_variety=lote.variedad_arroz,
        crop_age_days=lote.edad_cultivo_dias,
        area_ha=lote.area_ha,
        center_lat=lote.latitud_centro,
        center_lon=lote.longitud_centro,
        polygon_geojson=json.loads(lote.poligono_geojson),
    )
