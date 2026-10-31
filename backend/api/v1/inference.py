"""
Endpoints de Inferencia Visual Multinivel: Fotografía Móvil en Terreno y Ortomosaicos de Dron (/api/v1/inference).
"""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.orm import Session

from backend.core.database import (
    OrthomosaicJobORM,
    PhytosanitaryDetectionORM,
    get_db,
)
from backend.core.storage import storage_service
from backend.schemas.api_schemas import (
    FieldPredictionResponse,
    OrthomosaicJobResponse,
)
from backend.services.inference_service import inference_service
from backend.workers.celery_app import (
    execute_orthomosaic_analysis,
    process_orthomosaic_task,
)

router = APIRouter(prefix="/inference", tags=["Inferencia IA Multinivel (Móvil & Dron)"])

ALLOWED_IMAGE_TYPES = {
    "image/jpeg",
    "image/jpg",
    "image/png",
    "image/tiff",
    "application/octet-stream",
}


@router.post("/mobile", response_model=FieldPredictionResponse)
async def predict_mobile_field_image(
    file: UploadFile = File(..., description="Fotografía foliar o de plaga capturada en terreno (JPEG/PNG)"),
    lot_id: str = Form(default="LOTE-ESPINAL-01"),
    latitude: float = Form(default=4.1486),
    longitude: float = Form(default=-74.8830),
    db: Session = Depends(get_db),
):
    if file.content_type and file.content_type.lower() not in ALLOWED_IMAGE_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"Formato de archivo no soportado: {file.content_type}. Envíe JPEG o PNG.",
        )

    raw_bytes = await file.read()
    try:
        result = inference_service.predict(
            raw_bytes,
            lot_id=lot_id,
            latitude=latitude,
            longitude=longitude,
            source_type="MOBILE_ONLINE",
        )
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"No fue posible procesar la imagen: {exc}") from exc

    object_key = f"mobile/{lot_id}/{uuid.uuid4().hex[:12]}_{file.filename or 'capture.jpg'}"
    storage_service.save_bytes(object_key, raw_bytes, content_type=file.content_type or "image/jpeg")

    detection = PhytosanitaryDetectionORM(
        client_record_id=f"ONLINE-{uuid.uuid4().hex[:10]}",
        lot_id=lot_id,
        source_type="MOBILE_ONLINE",
        disease_label=result["disease_label"],
        confidence=result["confidence"],
        severity_index=result["severity_index"],
        latitude=latitude,
        longitude=longitude,
        point_wkt=f"POINT({longitude} {latitude})",
        model_version=result["model_version"],
    )
    db.add(detection)
    db.commit()

    return FieldPredictionResponse(**result)


@router.post("/orthomosaic", response_model=OrthomosaicJobResponse)
async def submit_drone_orthomosaic(
    file: UploadFile = File(..., description="Ortomosaico GeoTIFF o captura aérea de dron (VANT)"),
    lot_id: str = Form(default="LOTE-ESPINAL-01"),
    db: Session = Depends(get_db),
):
    raw_bytes = await file.read()
    if not raw_bytes:
        raise HTTPException(status_code=400, detail="El archivo de ortomosaico está vacío.")

    task_id = f"ORTHO-{uuid.uuid4().hex[:12].upper()}"
    ext = ".tif" if (file.filename or "").lower().endswith((".tif", ".tiff")) else ".jpg"
    object_key = f"orthomosaics/{lot_id}/{task_id}{ext}"
    saved_obj = storage_service.save_bytes(object_key, raw_bytes)

    job = OrthomosaicJobORM(
        task_id=task_id,
        lot_id=lot_id,
        status="PENDING",
        storage_object_key=object_key,
    )
    db.add(job)
    db.commit()

    try:
        process_orthomosaic_task.delay(task_id, lot_id, saved_obj["local_path"])
    except Exception:
        execute_orthomosaic_analysis(task_id, lot_id, saved_obj["local_path"])

    db.refresh(job)
    return OrthomosaicJobResponse(
        task_id=job.task_id,
        lot_id=job.lot_id,
        status=job.status,
        total_patches=job.total_patches,
        infested_patches=job.infested_patches,
        infection_rate=job.infection_rate,
        heatmap_geojson_url=f"/api/v1/geospatial/heatmap/{lot_id}",
        message="Ortomosaico procesado y capa de calor actualizada.",
    )


@router.get("/tasks/{task_id}", response_model=OrthomosaicJobResponse)
def get_orthomosaic_job_status(task_id: str, db: Session = Depends(get_db)):
    job = db.query(OrthomosaicJobORM).filter(OrthomosaicJobORM.task_id == task_id).first()
    if job is None:
        raise HTTPException(status_code=404, detail=f"No existe la tarea '{task_id}'")
    return OrthomosaicJobResponse(
        task_id=job.task_id,
        lot_id=job.lot_id,
        status=job.status,
        total_patches=job.total_patches,
        infested_patches=job.infested_patches,
        infection_rate=job.infection_rate,
        heatmap_geojson_url=f"/api/v1/geospatial/heatmap/{job.lot_id}",
        message=f"Estado de procesamiento: {job.status}",
    )
