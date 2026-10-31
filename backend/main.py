"""
Punto de Entrada Principal del Backend Empresarial PlagIA (FastAPI Asíncrono).

Integra:
- Inicialización única del motor de inferencia ONNX Runtime (GPU CUDA / CPU) + YOLO.
- Inicialización de la base de datos geoespacial (PostGIS / SQLite) con lotes del Tolima.
- Rutas RESTful `/api/v1/auth`, `/api/v1/farms`, `/api/v1/inference`, `/api/v1/sync` y `/api/v1/geospatial`.
"""

from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.api.v1 import auth, farms, geospatial, inference, sync
from backend.core.config import settings
from backend.core.database import (
    init_db_and_seed_tolima_lots,
    obtener_estado_motor_bd,
)
from backend.core.storage import storage_service
from backend.schemas.api_schemas import HealthStatusResponse
from backend.services.inference_service import inference_service
from ml_engine.config import AGRONOMIC_DISCLAIMER


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db_and_seed_tolima_lots()
    storage_service.try_connect_minio()
    inference_service.load()
    yield


app = FastAPI(
    title=settings.app_name,
    description=(
        "Plataforma Empresarial de Vigilancia Fitosanitaria Multinivel (Drones VANT + App Móvil "
        "Flutter Edge-AI) y Mapeo Geoespacial para el Cultivo de Arroz en el Tolima. "
        + AGRONOMIC_DISCLAIMER
    ),
    version=settings.version,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", response_model=HealthStatusResponse, tags=["Monitoreo e Infraestructura"])
@app.get("/api/v1/health", response_model=HealthStatusResponse, tags=["Monitoreo e Infraestructura"])
def health_check():
    hw = inference_service.get_hardware_status()
    db_type = obtener_estado_motor_bd()
    storage_type = "MinIO-S3" if storage_service.minio_active else "LocalObjectStore"
    return HealthStatusResponse(
        status="ok",
        app_name=settings.app_name,
        version=settings.version,
        model_loaded=inference_service.is_loaded(),
        active_engine=hw["active_engine"],
        cuda_available=hw["cuda_available"],
        gpu_name=hw["gpu_name"],
        vram_total_mb=hw["vram_total_mb"],
        database_status=f"connected ({db_type})",
        storage_backend=storage_type,
    )


app.include_router(auth.router, prefix="/api/v1")
app.include_router(farms.router, prefix="/api/v1")
app.include_router(inference.router, prefix="/api/v1")
app.include_router(sync.router, prefix="/api/v1")
app.include_router(geospatial.router, prefix="/api/v1")
