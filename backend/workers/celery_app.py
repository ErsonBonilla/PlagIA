"""
Worker Asíncrono Celery + Redis para Segmentación e Inferencia de Ortomosaicos GeoTIFF.

Si Redis no se encuentra activo en desarrollo local (`PLAGIA_CELERY_EAGER_FALLBACK=true`),
ejecuta el pipeline de forma síncrona/en proceso para garantizar operatividad continua.
"""

from __future__ import annotations

from pathlib import Path

from celery import Celery

from backend.core.config import settings
from backend.core.database import (
    OrthomosaicJobORM,
    PhytosanitaryDetectionORM,
    SessionLocal,
)
from backend.services.inference_service import inference_service
from ml_engine.config import ARTIFACTS_DIR
from ml_engine.geospatial import (
    build_heatmap_geodataframe,
    create_sample_orthomosaic_geotiff,
    export_heatmap_artifacts,
    slice_orthomosaic_into_patches,
)

celery_app = Celery(
    "plagia_enterprise_worker",
    broker=settings.redis_url,
    backend=settings.redis_url,
)
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="America/Bogota",
    enable_utc=True,
    task_always_eager=settings.celery_eager_fallback,
)


def execute_orthomosaic_analysis(task_id: str, lot_id: str, file_path_str: str) -> dict:
    """Secciona un ortomosaico GeoTIFF (o convierte imagen aérea), clasifica parches y genera el Mapa de Calor."""
    file_path = Path(file_path_str)
    if file_path.suffix.lower() not in {".tif", ".tiff"}:
        tif_target = ARTIFACTS_DIR / "orthomosaics" / f"{task_id}.tif"
        file_path = create_sample_orthomosaic_geotiff(
            tif_target,
            zone_key="EL_ESPINAL",
            source_images=[file_path] * 9,
        )

    patches = slice_orthomosaic_into_patches(file_path, patch_size=224)
    patch_predictions: list[dict] = []

    with SessionLocal() as db:
        job = db.query(OrthomosaicJobORM).filter(OrthomosaicJobORM.task_id == task_id).first()
        if job:
            job.status = "PROCESSING"
            db.commit()

        for p in patches:
            pred = inference_service.predict(
                p["image_rgb"],
                lot_id=lot_id,
                latitude=p["center_lat"],
                longitude=p["center_lon"],
                source_type="DRONE_ORTHOMOSAIC",
            )
            patch_predictions.append(
                {
                    "patch_id": p["patch_id"],
                    "disease_label": pred["disease_label"],
                    "confidence": pred["confidence"],
                    "bbox_gps": p["bbox_gps"],
                    "latitude": p["center_lat"],
                    "longitude": p["center_lon"],
                }
            )
            db.add(
                PhytosanitaryDetectionORM(
                    client_record_id=f"{task_id}-{p['patch_id']}",
                    lot_id=lot_id,
                    source_type="DRONE_ORTHOMOSAIC",
                    disease_label=pred["disease_label"],
                    confidence=pred["confidence"],
                    severity_index=pred["severity_index"],
                    latitude=p["center_lat"],
                    longitude=p["center_lon"],
                    point_wkt=f"POINT({p['center_lon']} {p['center_lat']})",
                    model_version=pred["model_version"],
                )
            )

        gdf = build_heatmap_geodataframe(patch_predictions, lot_id=lot_id)
        heatmap_summary = export_heatmap_artifacts(gdf, lot_id=lot_id)

        if job:
            job.status = "COMPLETED"
            job.total_patches = heatmap_summary["total_cells"]
            job.infested_patches = heatmap_summary["infested_cells"]
            job.infection_rate = heatmap_summary["infection_rate"]
            job.heatmap_geojson_path = heatmap_summary["geojson_path"]
            job.heatmap_png_path = heatmap_summary["png_path"]
        db.commit()

    return heatmap_summary


@celery_app.task(name="plagia.process_orthomosaic")
def process_orthomosaic_task(task_id: str, lot_id: str, file_path_str: str) -> dict:
    return execute_orthomosaic_analysis(task_id=task_id, lot_id=lot_id, file_path_str=file_path_str)
