"""
Endpoints Unificados de Mapas de Calor Geoespaciales (/api/v1/maps/heatmap/{farm_id}
y /api/v1/geospatial/heatmap/{lot_id}).

Aplica la Regla de Oro:
- Consultas internas sobre `FincaORM`, `LoteORM` y `DeteccionFitosanitariaORM` en español.
- Contratos HTTP REST y estándar RFC 7946 GeoJSON conservados en inglés.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.core.database import (
    DeteccionFitosanitariaORM,
    LoteORM,
    obtener_sesion_bd,
)
from backend.schemas.api_schemas import RespuestaMapaCalorGeoJSON
from ml_engine.config import AVISO_AGRONOMICO
from ml_engine.geospatial import (
    construir_geodataframe_mapa_calor,
    exportar_artefactos_mapa_calor,
)

router = APIRouter(tags=["Mapas de Calor Geoespaciales (GeoJSON / PostGIS)"])


def _generar_mapa_calor_lote(id_lote_o_finca: str, sesion: Session) -> RespuestaMapaCalorGeoJSON:
    lote = (
        sesion.query(LoteORM)
        .filter((LoteORM.id == id_lote_o_finca) | (LoteORM.finca_id == id_lote_o_finca))
        .first()
    )
    id_lote = lote.id if lote is not None else id_lote_o_finca
    municipio = lote.municipio if lote is not None else "El Espinal"

    detecciones = (
        sesion.query(DeteccionFitosanitariaORM)
        .filter(DeteccionFitosanitariaORM.lote_id == id_lote)
        .order_by(DeteccionFitosanitariaORM.id.desc())
        .limit(200)
        .all()
    )

    if not detecciones:
        puntos_muestra = [
            {
                "patch_id": "CELDA-01",
                "disease_label": "sano",
                "confidence": 0.95,
                "latitude": 4.1486,
                "longitude": -74.8830,
            }
        ]
    else:
        puntos_muestra = [
            {
                "patch_id": f"DET-{d.id:04d}",
                "disease_label": d.etiqueta_enfermedad,
                "confidence": d.confianza,
                "latitude": d.latitud,
                "longitude": d.longitud,
            }
            for d in detecciones
        ]

    gdf = construir_geodataframe_mapa_calor(puntos_muestra, lot_id=id_lote, municipio=municipio)
    resumen = exportar_artefactos_mapa_calor(gdf, lot_id=id_lote)

    return RespuestaMapaCalorGeoJSON(
        lot_id=id_lote,
        municipality=municipio,
        total_cells=resumen["total_cells"],
        infested_cells=resumen["infested_cells"],
        infection_rate=resumen["infection_rate"],
        mean_severity_index=resumen["mean_severity_index"],
        geojson=resumen["geojson"],
        disclaimer=AVISO_AGRONOMICO,
    )


@router.get("/maps/heatmap/{farm_id}", response_model=RespuestaMapaCalorGeoJSON)
def obtener_mapa_calor_por_finca_o_lote(
    farm_id: str, sesion: Session = Depends(obtener_sesion_bd)
):
    return _generar_mapa_calor_lote(id_lote_o_finca=farm_id, sesion=sesion)


@router.get("/geospatial/heatmap/{lot_id}", response_model=RespuestaMapaCalorGeoJSON)
def obtener_mapa_calor_fitosanitario_lote(
    lot_id: str, sesion: Session = Depends(obtener_sesion_bd)
):
    return _generar_mapa_calor_lote(id_lote_o_finca=lot_id, sesion=sesion)
