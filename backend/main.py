"""
Punto de Entrada Principal del Backend Empresarial PlagIA (FastAPI Asíncrono).

Aplica la Regla de Oro:
- Configuración, ciclo de inicialización de BD/modelos y mensajes visibles en español.
- Rutas del contrato REST (`/api/v1/*`, `/health`) e interfaz FastAPI (`lifespan`) en inglés.
"""

from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.api.v1 import auth, drones, farms, geospatial, inference, maps, sync
from backend.core.config import configuracion
from backend.core.database import (
    inicializar_bd_y_sembrar_lotes_tolima,
    obtener_estado_motor_bd,
)
from backend.core.storage import servicio_almacenamiento
from backend.schemas.api_schemas import RespuestaEstadoSalud
from backend.services.inference_service import inference_service
from ml_engine.config import AVISO_AGRONOMICO


@asynccontextmanager
async def lifespan(app: FastAPI):
    inicializar_bd_y_sembrar_lotes_tolima()
    servicio_almacenamiento.intentar_conectar_minio()
    inference_service.load()
    yield


app = FastAPI(
    title=configuracion.app_name,
    description=(
        "Plataforma Empresarial de Vigilancia Fitosanitaria Multinivel (Drones VANT + App Móvil "
        "Flutter Edge-AI) y Mapeo Geoespacial para el Cultivo de Arroz en el Tolima. "
        + AVISO_AGRONOMICO
    ),
    version=configuracion.version,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", response_model=RespuestaEstadoSalud, tags=["Monitoreo e Infraestructura"])
@app.get("/api/v1/health", response_model=RespuestaEstadoSalud, tags=["Monitoreo e Infraestructura"])
def verificar_salud_sistema():
    estado_hw = inference_service.get_hardware_status()
    motor_bd = obtener_estado_motor_bd()
    motor_almacenamiento = (
        "MinIO-S3 (Activo)"
        if servicio_almacenamiento.minio_activo
        else "Almacenamiento Local de Objetos"
    )
    return RespuestaEstadoSalud(
        status="ok",
        app_name=configuracion.app_name,
        version=configuracion.version,
        model_loaded=inference_service.is_loaded(),
        active_engine=estado_hw["active_engine"],
        cuda_available=estado_hw["cuda_available"],
        gpu_name=estado_hw["gpu_name"],
        vram_total_mb=estado_hw["vram_total_mb"],
        database_status=f"Conectado ({motor_bd})",
        storage_backend=motor_almacenamiento,
    )


app.include_router(auth.router, prefix="/api/v1")
app.include_router(farms.router, prefix="/api/v1")
app.include_router(inference.router, prefix="/api/v1")
app.include_router(drones.router, prefix="/api/v1")
app.include_router(sync.router, prefix="/api/v1")
app.include_router(geospatial.router, prefix="/api/v1")
app.include_router(maps.router, prefix="/api/v1")
