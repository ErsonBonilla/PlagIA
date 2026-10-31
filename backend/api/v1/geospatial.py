"""
Endpoints Geoespaciales y Generación de Mapas de Calor en Formato GeoJSON (/api/v1/geospatial).
"""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.core.database import LotORM, PhytosanitaryDetectionORM, get_db
from backend.schemas.api_schemas import HeatmapGeoJSONResponse
from ml_engine.config import AGRONOMIC_DISCLAIMER
from ml_engine.geospatial import (
    build_heatmap_geodataframe,
    export_heatmap_artifacts,
)

router = APIRouter(prefix="/geospatial", tags=["Mapas de Calor Geoespaciales (GeoPandas / PostGIS)"])


@router.get("/heatmap/{lot_id}", response_model=HeatmapGeoJSONResponse)
def get_lot_phytosanitary_heatmap(lot_id: str, db: Session = Depends(get_db)):
    lot = db.query(LotORM).filter(LotORM.id == lot_id).first()
    municipality = lot.municipality if lot else "El Espinal"

    detections = (
        db.query(PhytosanitaryDetectionORM)
        .filter(PhytosanitaryDetectionORM.lot_id == lot_id)
        .order_by(PhytosanitaryDetectionORM.id.desc())
        .limit(200)
        .all()
    )

    if not detections:
        sample_points = [
            {
                "patch_id": "CELDA-01",
                "disease_label": "sano",
                "confidence": 0.95,
                "latitude": 4.1486,
                "longitude": -74.8830,
            }
        ]
    else:
        sample_points = [
            {
                "patch_id": f"DET-{d.id:04d}",
                "disease_label": d.disease_label,
                "confidence": d.confidence,
                "latitude": d.latitude,
                "longitude": d.longitude,
            }
            for d in detections
        ]

    gdf = build_heatmap_geodataframe(sample_points, lot_id=lot_id, municipio=municipality)
    summary = export_heatmap_artifacts(gdf, lot_id=lot_id)

    return HeatmapGeoJSONResponse(
        lot_id=lot_id,
        municipality=municipality,
        total_cells=summary["total_cells"],
        infested_cells=summary["infested_cells"],
        infection_rate=summary["infection_rate"],
        mean_severity_index=summary["mean_severity_index"],
        geojson=summary["geojson"],
        disclaimer=AGRONOMIC_DISCLAIMER,
    )
