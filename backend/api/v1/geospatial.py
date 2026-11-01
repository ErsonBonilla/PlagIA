"""
Endpoints Geoespaciales y Generación de Mapas de Calor en Formato GeoJSON (/api/v1/geospatial).

Aplica la Regla de Oro:
- Consultas internas sobre `LoteORM` y `DeteccionFitosanitariaORM` en español.
- Estándar RFC 7946 GeoJSON (`FeatureCollection`, `features`, `geometry`, `properties`) en inglés.
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

router = APIRouter(prefix="/geospatial", tags=["Mapas de Calor Geoespaciales (GeoPandas / PostGIS)"])


@router.get("/heatmap/{lot_id}", response_model=RespuestaMapaCalorGeoJSON)
def obtener_mapa_calor_fitosanitario_lote(
    lot_id: str, sesion: Session = Depends(obtener_sesion_bd)
):
    lote = sesion.query(LoteORM).filter(LoteORM.id == lot_id).first()
    municipio = lote.municipio if lote else "El Espinal"

    detecciones = (
        sesion.query(DeteccionFitosanitariaORM)
        .filter(DeteccionFitosanitariaORM.lote_id == lot_id)
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

    gdf = construir_geodataframe_mapa_calor(puntos_muestra, lot_id=lot_id, municipio=municipio)
    resumen = exportar_artefactos_mapa_calor(gdf, lot_id=lot_id)

    return RespuestaMapaCalorGeoJSON(
        lot_id=lot_id,
        municipality=municipio,
        total_cells=resumen["total_cells"],
        infested_cells=resumen["infested_cells"],
        infection_rate=resumen["infection_rate"],
        mean_severity_index=resumen["mean_severity_index"],
        geojson=resumen["geojson"],
        disclaimer=AVISO_AGRONOMICO,
    )
