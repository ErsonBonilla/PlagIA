"""
Endpoints de Sincronización Offline-First y Actualización OTA para la App Móvil Flutter (/api/v1/sync).
"""

from __future__ import annotations

import json
from datetime import datetime, timezone

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.core.database import PhytosanitaryDetectionORM, get_db
from backend.schemas.api_schemas import (
    OfflineBatchSyncRequest,
    OfflineBatchSyncResponse,
)
from ml_engine.config import MODEL_METADATA_PATH, normalizar_etiqueta_espanol
from ml_engine.exporter import ensure_default_artifacts_exist

router = APIRouter(prefix="/sync", tags=["Sincronización Offline-First (Flutter Edge-AI)"])


@router.post("/batch", response_model=OfflineBatchSyncResponse)
def sync_offline_records_batch(payload: OfflineBatchSyncRequest, db: Session = Depends(get_db)):
    """Recibe el lote de diagnósticos recolectados sin internet por la App Flutter en el campo."""
    synced_ids: list[str] = []
    target_lot = "LOTE-ESPINAL-01"

    for item in payload.records:
        target_lot = item.lot_id
        etiqueta_es = normalizar_etiqueta_espanol(item.disease_label)
        existing = (
            db.query(PhytosanitaryDetectionORM)
            .filter(PhytosanitaryDetectionORM.client_record_id == item.client_record_id)
            .first()
        )
        if existing is None:
            db.add(
                PhytosanitaryDetectionORM(
                    client_record_id=item.client_record_id,
                    lot_id=item.lot_id,
                    source_type="MOVIL_OFFLINE",
                    disease_label=etiqueta_es,
                    confidence=item.confidence,
                    severity_index=item.severity_index,
                    latitude=item.latitude,
                    longitude=item.longitude,
                    point_wkt=f"POINT({item.longitude} {item.latitude})",
                    model_version=item.model_version,
                    captured_at=item.captured_at or datetime.now(timezone.utc),
                )
            )
        synced_ids.append(item.client_record_id)

    db.commit()

    lot_records = (
        db.query(PhytosanitaryDetectionORM)
        .filter(PhytosanitaryDetectionORM.lot_id == target_lot)
        .all()
    )
    total = len(lot_records)
    infested = sum(
        1 for r in lot_records if normalizar_etiqueta_espanol(r.disease_label) != "sano"
    )
    infection_rate = round(infested / max(1, total), 4)

    return OfflineBatchSyncResponse(
        device_id=payload.device_id,
        received_count=len(payload.records),
        synced_ids=synced_ids,
        lot_updated_infection_rate=infection_rate,
        server_timestamp=datetime.now(timezone.utc),
    )


@router.get("/mobile-model")
def get_mobile_edge_model_manifest():
    """Entrega el manifiesto OTA del modelo ONNX INT8 embebido para dispositivos Flutter."""
    if not MODEL_METADATA_PATH.exists():
        ensure_default_artifacts_exist()
    return json.loads(MODEL_METADATA_PATH.read_text(encoding="utf-8"))
