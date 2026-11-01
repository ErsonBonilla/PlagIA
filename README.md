# PlagIA Enterprise

**Plataforma de Vigilancia Fitosanitaria, Visión Computacional Multinivel y Geoprocesamiento para el Cultivo de Arroz en el Tolima**

PlagIA es una solución empresarial de agricultura de precisión diseñada para mitigar las pérdidas de productividad por plagas y enfermedades en los distritos arroceros del Tolima (El Espinal, Saldaña, Guamo, Purificación, Lérida e Ibagué). Integra análisis de imágenes capturadas por drones (VANTs) y fotografías tomadas en terreno con dispositivos móviles bajo una arquitectura **Offline-First**.

---

## 1. Stack Tecnológico Empresarial

| Capa | Tecnologías Implementadas |
|---|---|
| **Gestor de Entorno e Intérprete** | **`uv`** + **Python 3.12** (`.python-version`, `pyproject.toml`, sin dependencia de Conda) |
| **Aceleración por Hardware** | **CUDA sobre WSL 2** optimizado para **NVIDIA GeForce RTX 3050 (4 GB VRAM)** con Precisión Mixta Automática (`AMP FP16`) |
| **Motor de IA e Inferencia** | **PyTorch Core** (`ResNet50` / `EfficientNet-B0` con Transfer Learning en 2 fases), **Ultralytics (`YOLOv8`/`YOLOv11`)** y **ONNX Runtime (`CUDAExecutionProvider` / `INT8 Mobile`)** |
| **Preprocesamiento y Geoespacial** | **OpenCV** (corrección radiométrica `CLAHE`), **Albumentations**, **Rasterio** (ortomosaicos GeoTIFF) y **GeoPandas / Shapely** (Mapas de Calor y capas GeoJSON) |
| **MLOps y Gobernanza de Datos** | **PySpark / Pandas** (manifiesto multinivel y prevención de *Data Leakage*) + **MLflow Tracking & Model Registry** |
| **Backend y Procesamiento Asíncrono** | **FastAPI** (asíncrono, JWT, OpenAPI) + **Celery & Redis** (segmentación de ortomosaicos en segundo plano) |
| **Persistencia Espacial y Objetos** | **PostgreSQL 16 + PostGIS 3.4** (geometrías de lotes y focos de plaga) + **MinIO (S3 compatible)** |
| **Aplicación Móvil (Campo)** | **Flutter 3.47 / Dart 3.13** preparada para **Android Studio** (Inferencia local Edge-AI ONNX, GPS nativo offline, cola SQLite y visor de mapas de calor `flutter_map`) |
| **Contenerización** | **Docker & Docker Compose** con passthrough de GPU NVIDIA |

---

## 2. Estructura del Monorepo

```text
PlagIA/
├── .python-version              # Fijado en Python 3.12 para uv
├── pyproject.toml               # Definición de dependencias e índice oficial PyTorch CUDA (cu126)
├── Dockerfile                   # Imagen empresarial con uv + Python 3.12 + CUDA 12.6
├── docker-compose.yml           # Orquestación: api, celery_worker, redis, postgis, minio, mlflow
├── dataset/                     # Repositorio curado en 3 dominios (01_dron_dosel_cls, 02_campo_hoja_cls, 03_deteccion_plagas_yolo)
├── docs/
│   ├── RESUMEN_EJECUTIVO.md     # Caso de negocio, ROI, auditoría de datos y gobernanza agronómica
│   └── ARQUITECTURA.md          # Especificación de microservicios, PostGIS y protocolo Offline-First
├── scripts/
│   ├── wsl2_setup.sh            # Aprovisionamiento automático en WSL 2 (Ubuntu + uv + CUDA)
│   ├── check_wsl2_cuda.py       # Diagnóstico de GPU RTX 3050, Tensor Cores AMP FP16 y ONNX Runtime
│   └── setup_flutter_android.ps1# Vinculación con Android Studio y validación de Flutter/Dart
├── ml_engine/                   # Motor de IA, MLOps y Geoprocesamiento
│   ├── config.py                # Parámetros globales, clases fitosanitarias y polígonos del Tolima
│   ├── data_governance.py       # Manifiesto multinivel (Pandas + PySpark), control de leakage y split 70/15/15
│   ├── preprocessing.py         # Filtro radiométrico CLAHE (OpenCV), Albumentations y DataLoaders PyTorch
│   ├── architectures.py         # Redes PyTorch (Fase A congelada / Fase B fine-tuning) + Ultralytics YOLO
│   ├── trainer.py               # Entrenamiento con AMP FP16, liberación de VRAM y registro en MLflow
│   ├── evaluation.py            # Matriz de confusión, ROC-AUC, Precision, Recall, F1-Macro y curvas
│   ├── exporter.py              # Exportación a ONNX (Servidor + INT8 cuantizado para Flutter) y benchmark
│   ├── geospatial.py            # Tiling de ortomosaicos GeoTIFF (Rasterio) y Mapas de Calor (GeoPandas)
│   └── notebooks/               # Cuadernos reproducibles de ingeniería de modelos (01 al 04)
├── backend/                     # Plataforma Backend Empresarial (FastAPI + Celery + PostGIS + MinIO)
│   ├── main.py                  # Aplicación FastAPI con lifespan, monitoreo de GPU y rutas /api/v1
│   ├── core/                    # Configuración, Seguridad JWT, Base de Datos PostGIS/SQLite y Storage MinIO
│   ├── schemas/                 # Contratos Pydantic de peticiones y respuestas
│   ├── services/                # Servicio singleton de inferencia (ONNX Runtime / PyTorch / YOLO)
│   ├── workers/                 # Tareas asíncronas Celery + Redis para ortomosaicos de dron
│   └── api/v1/                  # Endpoints: auth, farms, inference, sync (Flutter offline) y geospatial
├── mobile_app/                  # Aplicación Móvil Offline-First en Flutter (Dart) para Android Studio
│   ├── pubspec.yaml             # Configuración Dart ^3.13.0 y paquetes de campo
│   ├── android/                 # Proyecto Android preconfigurado (Permisos Cámara, GPS y Tráfico Local)
│   ├── assets/models/           # Modelo ONNX INT8 embebido + catálogo fitosanitario del Tolima
│   └── lib/                     # Código Dart: modelos, servicios Edge-AI/GPS/Sync y pantallas
└── tests/
    └── test_plagia_platform.py  # Suite de pruebas automatizadas E2E (pytest)
```

---

## 3. Guía Rápida de Inicio (con `uv` y Python 3.12)

### A. En WSL 2 (Ubuntu) con aceleración CUDA
```bash
# 1. Ejecutar el script de preparación y diagnóstico CUDA
bash scripts/wsl2_setup.sh

# 2. O manualmente con uv:
uv python install 3.12
uv sync --python 3.12
uv run python scripts/check_wsl2_cuda.py
```

### B. En Windows PowerShell con `uv`
```powershell
uv python install 3.12
uv sync --python 3.12
uv run python scripts/check_wsl2_cuda.py
```

### C. Ejecutar el Pipeline de Ingeniería de IA y Exportación ONNX
Puedes ejecutar los 4 cuadernos en orden dentro de `ml_engine/notebooks/` (`01` $\rightarrow$ `04`) con `uv run jupyter lab`, o correr las pruebas e inicialización rápida desde terminal:
```bash
# Levantar interfaz de MLflow Tracking & Registry
uv run mlflow ui --backend-store-uri sqlite:///mlflow.db --port 5000

# Levantar el Backend Empresarial FastAPI
uv run uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
# Documentación interactiva OpenAPI: http://localhost:8000/docs
```

### D. Despliegue Completo con Docker Compose (PostGIS + Redis + Celery + MinIO + API GPU)
```bash
docker compose up --build -d
```

### E. Abrir y Compilar la App Móvil en Android Studio
1. Ejecuta el script de verificación:
   ```powershell
   .\scripts\setup_flutter_android.ps1
   ```
2. Abre **Android Studio** $\rightarrow$ **Open** $\rightarrow$ selecciona la carpeta `C:\Users\erson\Documents\Programación\ISIDEAD\PlagIA\mobile_app`.
3. Inicia un emulador desde el **Device Manager** (la app se conectará automáticamente a `http://10.0.2.2:8000/api/v1` cuando haya red y operará en modo **Edge-AI Offline** cuando no exista conectividad).

---

## 4. Verificación Automatizada (Tests)
```bash
uv run pytest tests/ -v
```
