"""
Esquemas Pydantic v2 para los Contratos OpenAPI del Backend Empresarial PlagIA.

Aplica la Regla de Oro:
- Clases internas de esquema, descripciones y ejemplos visibles en OpenAPI/Swagger en español.
- Nombres de campos del contrato JSON externo conservados en inglés.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class SolicitudToken(BaseModel):
    username: str = Field(..., description="Correo corporativo del operador", examples=["agronomo@plagia.co"])
    password: str = Field(..., description="Contraseña corporativa", examples=["PlagIA2026*"])


class RespuestaToken(BaseModel):
    access_token: str = Field(..., description="Token JWT firmado")
    token_type: str = Field(default="bearer", description="Tipo de esquema de autenticación OAuth2")
    role: str = Field(..., description="Rol asignado dentro de PlagIA")
    district: str = Field(..., description="Distrito arrocero del Tolima")
    full_name: str = Field(..., description="Nombre completo del profesional")


class RespuestaEstadoSalud(BaseModel):
    status: str = Field(default="ok", description="Estado operativo del servicio")
    app_name: str = Field(..., description="Nombre del sistema empresarial")
    version: str = Field(..., description="Versión desplegada")
    model_loaded: bool = Field(..., description="Indica si el modelo ONNX está cargado en memoria")
    active_engine: str = Field(..., description="Proveedor de inferencia activo (CUDA / CPU)")
    cuda_available: bool = Field(..., description="Indica si la aceleración GPU NVIDIA está disponible")
    gpu_name: str | None = Field(default=None, description="Modelo de GPU detectado")
    vram_total_mb: float = Field(default=0.0, description="Memoria de video total en MiB")
    database_status: str = Field(..., description="Estado y motor activo de base de datos (PostgreSQL/PostGIS o SQLite)")
    storage_backend: str = Field(..., description="Almacenamiento de objetos activo (MinIO S3 o Local)")


class EsquemaCajaDelimitadora(BaseModel):
    bbox_xyxy: list[float] = Field(..., description="Coordenadas [x1, y1, x2, y2] del foco fitosanitario")
    confidence: float = Field(..., description="Confianza de localización (0.0 a 1.0)")
    label: str = Field(..., description="Etiqueta fitosanitaria en español", examples=["roya_parda"])
    detector: str = Field(..., description="Motor detector utilizado")


class RespuestaPrediccionCampo(BaseModel):
    lot_id: str = Field(..., description="Identificador del lote arrocero en el Tolima")
    source_type: str = Field(..., description="Fuente de captura (MOVIL_EN_LINEA, DRON_VANT)")
    disease_label: str = Field(..., description="Etiqueta fitosanitaria diagnosticada en español", examples=["roya_parda"])
    common_name: str = Field(..., description="Nombre común de la patología en el Tolima")
    causal_agent: str = Field(..., description="Agente fitopatógeno causal")
    confidence: float = Field(..., description="Probabilidad asignada a la clase ganadora")
    severity_index: float = Field(..., description="Índice ponderado de severidad fitosanitaria (0.0 a 1.0)")
    risk_level: str = Field(..., description="Nivel de riesgo fitosanitario (BAJO, MEDIO, ALTO, CRITICO)")
    mip_recommendation: str = Field(..., description="Recomendación de Manejo Integrado de Plagas (MIP)")
    probabilities: dict[str, float] = Field(..., description="Distribución de probabilidades por clase en español")
    bounding_boxes: list[EsquemaCajaDelimitadora] = Field(..., description="Cajas delimitadoras de lesiones localizadas")
    latitude: float = Field(..., description="Latitud GPS (EPSG:4326)")
    longitude: float = Field(..., description="Longitud GPS (EPSG:4326)")
    model_version: str = Field(..., description="Versión del modelo que ejecutó el diagnóstico")
    inference_time_ms: float = Field(..., description="Tiempo de inferencia en milisegundos")
    disclaimer: str = Field(..., description="Aviso agronómico legal obligatorio")


class RespuestaTrabajoOrtomosaico(BaseModel):
    task_id: str = Field(..., description="Identificador único del trabajo de ortomosaico")
    lot_id: str = Field(..., description="Identificador del lote arrocero")
    status: str = Field(..., description="Estado del procesamiento (PENDIENTE, PROCESANDO, COMPLETADO)")
    total_patches: int = Field(..., description="Total de parches georreferenciados analizados")
    infested_patches: int = Field(..., description="Parches con presencia de patología o plaga")
    infection_rate: float = Field(..., description="Proporción de infestación del lote (0.0 a 1.0)")
    heatmap_geojson_url: str = Field(..., description="Ruta para consultar el mapa de calor GeoJSON")
    message: str = Field(..., description="Mensaje descriptivo en español para el usuario")


class ElementoInspeccionOffline(BaseModel):
    client_record_id: str = Field(..., examples=["MOVIL-OFFLINE-2026-001"])
    lot_id: str = Field(default="LOTE-ESPINAL-01")
    disease_label: str = Field(..., examples=["roya_parda"])
    confidence: float = Field(..., ge=0.0, le=1.0)
    severity_index: float = Field(default=0.75, ge=0.0, le=1.0)
    latitude: float = Field(..., examples=[4.1486])
    longitude: float = Field(..., examples=[-74.8830])
    captured_at: datetime | None = None
    model_version: str = Field(default="1.0.0-edge-int8")


class SolicitudSincronizacionLoteOffline(BaseModel):
    device_id: str = Field(..., examples=["ANDROID-TOLIMA-CAMPO-01"])
    records: list[ElementoInspeccionOffline]


class RespuestaSincronizacionLoteOffline(BaseModel):
    device_id: str
    received_count: int
    synced_ids: list[str]
    lot_updated_infection_rate: float
    server_timestamp: datetime


class EsquemaResumenLote(BaseModel):
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


class RespuestaMapaCalorGeoJSON(BaseModel):
    lot_id: str
    municipality: str
    total_cells: int
    infested_cells: int
    infection_rate: float
    mean_severity_index: float
    geojson: dict[str, Any]
    disclaimer: str


# Alias de compatibilidad
TokenRequest = SolicitudToken
TokenResponse = RespuestaToken
HealthStatusResponse = RespuestaEstadoSalud
BoundingBoxSchema = EsquemaCajaDelimitadora
FieldPredictionResponse = RespuestaPrediccionCampo
OrthomosaicJobResponse = RespuestaTrabajoOrtomosaico
OfflineInspectionItem = ElementoInspeccionOffline
OfflineBatchSyncRequest = SolicitudSincronizacionLoteOffline
OfflineBatchSyncResponse = RespuestaSincronizacionLoteOffline
LotSummarySchema = EsquemaResumenLote
HeatmapGeoJSONResponse = RespuestaMapaCalorGeoJSON
