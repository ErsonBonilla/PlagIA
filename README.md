# PlagIA Enterprise

**Plataforma de Vigilancia Fitosanitaria, Visión Computacional Multinivel y Geoprocesamiento para el Cultivo de Arroz en el Tolima**

PlagIA está organizada en **3 componentes principales desacoplados** en la raíz del proyecto para máxima claridad arquitectónica:

```text
PlagIA/
├── backend/                     # COMPONENTE 1: Servidor API (FastAPI), Motor IA (PyTorch CUDA/YOLO/ONNX), Datasets y PostGIS/SQLite
│   ├── api/v1/                  # Endpoints REST: auth, farms, inference, drones, maps, sync
│   ├── core/                    # ConfiguracionEmpresarial, Seguridad JWT, BD Dual (PostGIS/SQLite) y MinIO
│   ├── engine/                  # Motor de IA y Geoprocesamiento (PyTorch, YOLO, ONNX, Rasterio, GeoPandas, notebooks/)
│   ├── dataset/                 # 3 Dominios curados (01_dron_dosel_cls, 02_campo_hoja_cls, 03_deteccion_plagas_yolo)
│   ├── models/                  # Modelos ONNX INT8 (4.5 MB) y auditoría neuronal
│   ├── runtime/                 # Bases locales y artefactos en tiempo de ejecución (SQLite, MLflow, mapas de calor)
│   ├── scripts/                 # Aprovisionamiento WSL 2, curaduría de datasets y entrenamiento GPU
│   ├── tests/                   # Suite de pruebas automatizadas E2E (test_plagia_platform.py)
│   ├── docs/                    # RESUMEN_EJECUTIVO.md y ARQUITECTURA.md
│   ├── main.py                  # Punto de entrada FastAPI
│   └── pyproject.toml           # Gestión de dependencias Python 3.12 con uv + PyTorch CUDA
│
├── frontend/                    # COMPONENTE 2: Portal Web SSR con Islas (Deno 2.9.5 + TypeScript 6.0.3 + Leaflet)
│   ├── islands/                 # MapViewer.tsx (Leaflet + espectro Grad-CAM) y AnalyticsDashboard.tsx (FEDEARROZ/AGROSAVIA)
│   ├── routes/                  # /dashboard, /lotes, /mapas, /reportes
│   ├── static/                  # styles.css (Sistema de diseño cromático WCAG AA)
│   ├── tests/                   # portal_test.ts
│   ├── deno.json
│   └── main.ts
│
├── mobile/                      # COMPONENTE 3: Aplicación Móvil Offline-First (Flutter 3.47.9 + Dart 3.13.7 para Android Studio)
│   ├── android/                 # Proyecto nativo Android preconfigurado
│   ├── assets/models/           # Modelo ONNX INT8 embebido + catálogo fitosanitario del Tolima
│   ├── lib/                     # main.dart, theme/ (Material 3), screens/ (Guías de encuadre), services/ y models/
│   ├── test/                    # widget_test.dart
│   └── pubspec.yaml
│
├── docker-compose.yml           # Orquestación general (postgis, redis, minio, mlflow, api, celery_worker, frontend)
└── README.md                    # Este documento
```

---

## Guía Rápida de Ejecución por Componente

### 1. Componente `backend/` (Python 3.12 + `uv` + PyTorch CUDA + FastAPI)
```powershell
cd backend
uv sync --python 3.12
uv run uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
# Pruebas automatizadas del backend y motor IA:
uv run pytest
```

### 2. Componente `frontend/` (Deno 2.9.5 + SSR Islands)
```powershell
cd frontend
deno task start
# Verificar tipos y pruebas del portal web:
deno task check
deno task test
```

### 3. Componente `mobile/` (Flutter 3.47.9 + Dart 3.13.7 en Android Studio)
```powershell
cd mobile
flutter pub get
dart analyze
flutter test
```
Para compilar en **Android Studio**, abre directamente la carpeta `C:\Users\erson\Documents\Programación\ISIDEAD\PlagIA\mobile`.

### 4. Despliegue Completo con Docker Compose (Desde la raíz `PlagIA/`)
```bash
docker compose up --build -d
```
