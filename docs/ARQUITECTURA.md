# Especificación de Arquitectura Empresarial - PlagIA

## 1. Visión de Componentes y Capas

La plataforma **PlagIA** sigue una arquitectura hexagonal y de microservicios contenerizados, dividida en tres subsistemas desacoplados:

1. **`ml_engine/` (Subsistema de Inteligencia Artificial, MLOps y Geoprocesamiento):**
   * Responsable de la ingesta gobernada desde `dataset/`, preprocesamiento radiométrico con OpenCV (`CLAHE`) y Albumentations, entrenamiento con **PyTorch (AMP FP16)** y **Ultralytics YOLO**, seguimiento en **MLflow**, exportación/cuantización **ONNX** y generación de **Mapas de Calor Geoespaciales** con Rasterio y GeoPandas.
2. **`backend/` (Subsistema Backend API y Procesamiento Asíncrono):**
   * Construido sobre **FastAPI**, **Celery + Redis**, **PostgreSQL + PostGIS** y **MinIO**. Incluye modo de alta disponibilidad híbrido: opera conectándose al clúster de contenedores Docker o en modo autónomo local (fallback transparente a SQLite/disco y ejecución en proceso) para desarrollo ágil y pruebas CI/CD.
3. **`frontend/` (Subsistema Portal Web SSR con Arquitectura de Islas en Deno 2.9.5 / TypeScript 6.0.3):**
   * Portal institucional de bajo consumo de ancho de banda con rutas `/dashboard`, `/lotes`, `/mapas`, `/reportes` e islas interactivas `islands/MapViewer.tsx` (Leaflet + espectro Grad-CAM) e `islands/AnalyticsDashboard.tsx` (FEDEARROZ / AGROSAVIA).
4. **`mobile/` (Subsistema Móvil Offline-First en Flutter 3.47.9 / Dart 3.13.7):**
   * Aplicación nativa multiplataforma (Android / iOS) preparada para **Android Studio**. Ejecuta inferencia en el borde (**Edge-AI**), captura coordenadas GPS sin señal celular, almacena inspecciones en **SQLite** y renderiza los mapas de calor GeoJSON sobre el lote arrocero.

---

## 2. Flujo de Procesamiento de Ortomosaicos (VANT / Dron)

```text
[Ortomosaico GeoTIFF / Imagen Aérea]
       │
       ▼  POST /api/v1/inference/orthomosaic
[FastAPI Gateway] ──► Almacena archivo crudo en MinIO S3 (o storage_local/)
       │
       ▼  Encola tarea asíncrona (task_id)
[Celery Worker + Redis]
       │
       ├──► 1. Rasterio divide el ortomosaico en parches (224x224) conservando su transformación afín (GPS)
       ├──► 2. OpenCV aplica corrección radiométrica CLAHE a cada parche
       ├──► 3. ONNX Runtime (CUDAExecutionProvider / CPU) clasifica cada parche y calcula severidad (0.0 - 1.0)
       ├──► 4. GeoPandas construye el GeoDataFrame (EPSG:4326) y calcula el índice de infestación por zona
       └──► 5. Persiste geometrías en PostGIS y exporta el Mapa de Calor (GeoJSON + PNG)
```

---

## 3. Protocolo de Sincronización Rural Offline-First (Flutter $\leftrightarrow$ FastAPI)

1. **En el lote arrocero (Sin conexión a internet):**
   * El agricultor o monitor fitosanitario toma una fotografía de la hoja de arroz con `FieldScannerScreen`.
   * `GpsService` obtiene latitud, longitud y precisión en metros directamente del chip GPS del dispositivo.
   * `EdgeInferenceService` ejecuta el modelo cuantizado `assets/models/plagia_mobile_int8.onnx` localmente en menos de 80 ms, entregando diagnóstico, confianza y recomendación de manejo inmediato.
   * `OfflineSyncService` guarda el registro en la tabla local SQLite `inspection_queue` con estado `PENDING_SYNC`.
2. **En el casco urbano o campamento (Con conexión Wi-Fi / 4G):**
   * `OfflineSyncService` empaqueta los registros pendientes y los envía a `POST /api/v1/sync/batch`.
   * El backend inserta las observaciones georreferenciadas en **PostGIS**, recalcula los focos de calor del lote y devuelve los identificadores confirmados (`synced_ids`) junto con la versión vigente del modelo móvil (`GET /api/v1/sync/mobile-model`).

---

## 4. Modelo de Datos Geoespacial (PostGIS / SQLAlchemy)

* **`farms` (Fincas Arroceras):** `id`, `name`, `municipality` (Espinal, Saldaña, Guamo, Purificación, Lérida, Ibagué), `owner_name`, `total_area_ha`, `created_at`.
* **`lots` (Lotes de Cultivo):** `id`, `farm_id`, `code`, `rice_variety` (ej. Fedearroz 67, Fedearroz 2000, ADT45), `crop_age_days`, `polygon_geojson` (`Geometry(POLYGON, 4326)`).
* **`phytosanitary_detections` (Detecciones Georreferenciadas):** `id`, `lot_id`, `source_type` (`DRONE` | `MOBILE_OFFLINE` | `MOBILE_ONLINE`), `disease_label`, `confidence`, `severity_index`, `latitude`, `longitude`, `point_wkt` (`Geometry(POINT, 4326)`), `captured_at`, `model_version`.
* **`orthomosaic_jobs` (Tareas Asíncronas de Mapeo Aéreo):** `task_id`, `lot_id`, `status` (`PENDING` | `PROCESSING` | `COMPLETED` | `FAILED`), `total_patches`, `infested_patches`, `infection_rate`, `heatmap_geojson_path`, `heatmap_image_path`.
