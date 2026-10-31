"""
Esquemas Pydantic v2 para los Contratos OpenAPI del Backend Empresarial PlagIA.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class TokenRequest(BaseModel):
    username: str = Field(..., examples=["agronomo@plagia.co"])
    password: str = Field(..., examples=["PlagIA2026*"])


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: str
    district: str
    full_name: str


class HealthStatusResponse(BaseModel):
    status: str = "ok"
    app_name: str
    version: str
    model_loaded: bool
    active_engine: str
    cuda_available: bool
    gpu_name: str | None = None
    vram_total_mb: float = 0.0
    database_status: str
    storage_backend: str


class BoundingBoxSchema(BaseModel):
    bbox_xyxy: list[float] = Field(..., description="Coordenadas [x1, y1, x2, y2] del foco fitosanitario")
    confidence: float
    label: str
    detector: str


class FieldPredictionResponse(BaseModel):
    lot_id: str
    source_type: str
    disease_label: str
    common_name: str
    causal_agent: str
    confidence: float
    severity_index: float
    risk_level: str
    mip_recommendation: str
    probabilities: dict[str, float]
    bounding_boxes: list[BoundingBoxSchema]
    latitude: float
    longitude: float
    model_version: str
    inference_time_ms: float
    disclaimer: str


class OrthomosaicJobResponse(BaseModel):
    task_id: str
    lot_id: str
    status: str
    total_patches: int
    infested_patches: int
    infection_rate: float
    heatmap_geojson_url: str
    message: str


class OfflineInspectionItem(BaseModel):
    client_record_id: str = Field(..., examples=["MOB-OFFLINE-2026-001"])
    lot_id: str = Field(default="LOTE-ESPINAL-01")
    disease_label: str = Field(..., examples=["brown_rust"])
    confidence: float = Field(..., ge=0.0, le=1.0)
    severity_index: float = Field(default=0.75, ge=0.0, le=1.0)
    latitude: float = Field(..., examples=[4.1486])
    longitude: float = Field(..., examples=[-74.8830])
    captured_at: datetime | None = None
    model_version: str = Field(default="1.0.0-edge-int8")


class OfflineBatchSyncRequest(BaseModel):
    device_id: str = Field(..., examples=["ANDROID-TOLIMA-FIELD-01"])
    records: list[OfflineInspectionItem]


class OfflineBatchSyncResponse(BaseModel):
    device_id: str
    received_count: int
    synced_ids: list[str]
    lot_updated_infection_rate: float
    server_timestamp: datetime


class LotSummarySchema(BaseModel):
    id: str
    farm_id: str
    name: str
    municipality: str
    rice_variety: str
    crop_age_days: int
    area_ha: float
    center_lat: float
    center_lon: float
    polygon_geojson: dict[str, Any]


class HeatmapGeoJSONResponse(BaseModel):
    lot_id: str
    municipality: str
    total_cells: int
    infested_cells: int
    infection_rate: float
    mean_severity_index: float
    geojson: dict[str, Any]
    disclaimer: str
