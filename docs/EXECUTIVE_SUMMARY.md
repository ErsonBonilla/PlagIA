# Resumen Ejecutivo Empresarial: Plataforma PlagIA

**Sistema de Inteligencia Fitosanitaria, Reconocimiento Visual Multinivel y Geoprocesamiento para el Cultivo de Arroz en el Departamento del Tolima**

---

## 1. Problema de Negocio y Contexto Agroindustrial

El departamento del Tolima (en particular la meseta de Ibagué y los distritos de riego de Usocoello, Saldaña, El Espinal, Guamo, Purificación y Lérida) constituye una de las zonas arroceras más productivas de Colombia. Sin embargo, las infestaciones fitosanitarias provocadas por patógenos fúngicos (*Pyricularia oryzae* / Añublo o Blast, *Bipolaris oryzae* / Mancha parda, *Puccinia* spp. / Royas), bacterias (*Xanthomonas oryzae* / Añublo bacteriano) e insectos plaga (*Sogatodes orizicola*, barrenadores del tallo *Diatraea* / *Rupela* y comedores de follaje *Spodoptera*) generan pérdidas de rendimiento de entre el **15% y el 40% por cosecha** cuando la detección ocurre de manera tardía.

El monitoreo tradicional depende de recorridos manuales por muestreo en lotes de decenas de hectáreas, lo que produce dos fallos críticos:
1. **Baja cobertura espacial y demora diagnóstica:** Los focos primarios en el interior del lote pasan desapercibidos hasta que la infestación supera el umbral económico de daño.
2. **Aplicación indiscriminada de agroquímicos:** Ante la ausencia de mapas precisos de concentración de plaga, se realizan fumigaciones generalizadas en todo el lote, incrementando los costos operativos por hectárea y el impacto ambiental.

**PlagIA** resuelve esta problemática mediante una plataforma empresarial de agricultura de precisión que articula captura con drones (VANTs), diagnóstico en terreno sin internet mediante dispositivos móviles (**Flutter Edge-AI**) y generación automatizada de **mapas de calor geoespaciales** para fumigación focalizada.

---

## 2. Gobernanza de Datos y Fuentes Multinivel

La plataforma opera sobre un repositorio de datos multinivel ubicado en `dataset/`, estructurado bajo reglas estrictas de gobernanza y trazabilidad:

| Nivel de Captura | Fuente / Dataset Integrado | Volumen | Categorías Fitosanitarias |
|---|---|---|---|
| **Nivel Aéreo (VANT / Dron)** | *Rice Crop Diseases Drone Captured Dataset* | 3,727 imágenes | `healthy`, `brown_rust`, `yellow_rust`, `ground` |
| **Nivel Terreno (Foliar Móvil)** | *Paddy Doctor Disease Classification* | 10,407 imágenes + metadatos (`variety`, `age`) | 10 clases (`blast`, `bacterial_leaf_blight`, `brown_spot`, `tungro`, `hispa`, `dead_heart`, `normal`, etc.) |
| **Nivel Entomológico (Plagas)** | *Rice Agricultural Pests Dataset* | 991 imágenes | 9 órdenes/especies (`stem_borer`, `armyworm`, `aphids`, `mites`, `grasshopper`, etc.) |

### Hallazgo Crítico de Auditoría de Datos (Prevención de *Data Leakage*)
Durante la auditoría automatizada implementada en `ml_engine/data_governance.py`, se identificó que el particionado `Train/` y `Test/` original del dataset de drones contiene:
1. **Archivos duplicados exactos** (sufijos ` - Copy.jpg` dentro de las carpetas de entrenamiento).
2. **Aumentaciones offline cruzadas (`augmented__<capture_id>_<hash>.jpg`):** Múltiples variaciones generadas a partir de la misma captura base aparecen simultáneamente en `Train/` y `Test/`.

Si se entrenara respetando las carpetas de origen, el modelo memorizaría la textura del lote original y reportaría métricas artificialmente infladas. Por ello, **PlagIA unifica todo el inventario, elimina copias redundantes, extrae el identificador de captura raíz (`group_id`) y ejecuta un particionado propio `70% Train / 15% Val / 15% Test` agrupado por entidad**, garantizando cero fuga de información entre particiones.

---

## 3. Justificación de la Arquitectura Tecnológica

La arquitectura de **PlagIA** fue diseñada bajo cuatro restricciones operativas reales del sector arrocero tolimense:

1. **Entorno de Desarrollo y Cómputo (`uv` + Python 3.12 + CUDA en WSL 2):**
   * Gestión determinista de dependencias sin sobrecarga de Conda mediante `uv` y `pyproject.toml`.
   * Aprovechamiento directo de GPU NVIDIA (**GeForce RTX 3050 de 4 GB VRAM**) sobre WSL 2 mediante **Precisión Mixta Automática (`AMP FP16`)** y acumulación de gradientes.
2. **Reconocimiento Visual Híbrido (`PyTorch` + `Ultralytics YOLO` + `ONNX Runtime`):**
   * **Redes Convolucionales con Transfer Learning (`ResNet50` / `EfficientNet-B0`)** para clasificación fina de patologías foliares y aéreas.
   * **Arquitectura en tiempo real (`YOLOv8` / `YOLOv11`)** para localización espacial de lesiones e insectos mediante cajas delimitadoras (*bounding boxes*).
   * **Exportación a `ONNX` (FP32/FP16 para servidor y cuantización `INT8` para móvil):** Reduce el tamaño del modelo en más de un 70% y multiplica la velocidad de inferencia.
3. **Procesamiento Geoespacial y Asíncrono (`Rasterio` + `GeoPandas` + `Celery/Redis` + `PostGIS` + `MinIO`):**
   * Los ortomosaicos GeoTIFF capturados por drones abarcan múltiples hectáreas y no pueden procesarse de forma síncrona en una petición HTTP. **FastAPI** delega la tarea a **Celery + Redis**, el cual divide el ortomosaico en parches georreferenciados con **Rasterio**, ejecuta la inferencia por lotes y construye capas **GeoJSON** en **PostGIS** que diferencian zonas sanas de focos de infestación.
4. **Aplicación Móvil Offline-First en `Flutter (Dart)`:**
   * En las veredas arroceras del Tolima la cobertura 4G/5G es intermitente o nula. La app móvil en **Flutter** ejecuta el modelo **ONNX INT8 localmente en el teléfono (Edge-AI)**, captura coordenadas GPS nativas sin requerir datos móviles, almacena los diagnósticos en **SQLite** y sincroniza automáticamente el lote (`POST /api/v1/sync/batch`) cuando el agrónomo regresa a una zona con conectividad.

---

## 4. Diseño del Modelo y Estrategia de Entrenamiento en Dos Fases

El motor `ml_engine/architectures.py` implementa Transfer Learning sobre pesos preentrenados en ImageNet siguiendo una estrategia industrial de dos etapas registradas en **MLflow**:

* **Fase A (Backbone Congelado - Adaptación del Cabezal Fitosanitario):** Se congelan todas las capas convolucionales base y se entrena únicamente el cabezal clasificador (`GlobalAveragePooling` $\rightarrow$ `BatchNorm` $\rightarrow$ `Dropout` $\rightarrow$ `Linear`) con tasa de aprendizaje moderada (`1e-3`). Esto estabiliza los pesos iniciales sin destruir los extractores de bordes y texturas.
* **Fase B (Fine-Tuning Selectivo con Preprocesamiento CLAHE):** Se descongelan los bloques profundos (`layer4` en ResNet50 / bloques superiores en EfficientNet) con un *learning rate* reducido (`1e-4` a `1e-5`), adaptando los filtros a la reflectancia clorofílica del arroz previamente normalizada mediante ecualización adaptativa de histograma **CLAHE en espacio LAB (OpenCV)**.

---

## 5. Métricas de Desempeño y Criterio de Selección

En vigilancia fitosanitaria, evaluar únicamente con *Accuracy* es riesgoso: omitir un foco primario de *Piricularia* o *Roya* (**Falso Negativo**) permite la propagación exponencial del patógeno hacia lotes vecinos. Por tanto, el criterio corporativo de selección en `ml_engine/evaluation.py` prioriza:
1. **F1-Score Macro:** Equilibrio global entre precisión y sensibilidad en todas las clases fitosanitarias.
2. **Recall de Clases Críticas (Sensibilidad Fitosanitaria):** Maximizar la detección de hojas/parches enfermos.
3. **ROC-AUC Multiclase (One-vs-Rest):** Capacidad discriminativa independientemente del umbral de corte.
4. **Latencia de Inferencia (ms/imagen):** Verificada mediante benchmark comparativo entre PyTorch nativo y ONNX Runtime.

---

## 6. Trazabilidad MLOps y Promoción en Model Registry

Cada experimento ejecutado en `03_training_pytorch_yolo_mlflow.ipynb` registra en **MLflow (`sqlite:///mlflow.db`)**:
* Hiperparámetros completos, configuración de hardware (GPU/VRAM, AMP FP16) y pesos de clase.
* Curvas de convergencia por época (`train_loss`, `val_loss`, `val_f1_macro`).
* Artefactos visuales: Matriz de Confusión normalizada, Curvas ROC por patología y reporte tabular.
* Firma formal de entrada/salida (*Model Signature*).

En `04_registry_onnx_and_heatmaps.ipynb`, el modelo con mayor **F1-Macro y Recall** se registra formalmente como `plagia_rice_classifier`, se promueve al stage **`Staging`** y se compila automáticamente a `models/plagia_server.onnx` y `models/plagia_mobile_int8.onnx` (sincronizado también hacia `mobile_app/assets/models/`).

---

## 7. Arquitectura de Producción y Despliegue Rural

El sistema completo se despliega mediante `docker-compose.yml` integrando seis servicios aislados:
1. **`plagia-api` (FastAPI + Uvicorn + GPU):** Expone endpoints REST autenticados con JWT para gestión de fincas/lotes, inferencia móvil, carga de ortomosaicos, sincronización offline y entrega de mapas de calor GeoJSON.
2. **`plagia-celery-worker` (Celery + GPU):** Ejecuta la segmentación por parches y actualización de capas geoespaciales en segundo plano.
3. **`plagia-redis` (Redis 7):** Broker de mensajería y caché de estados de tareas.
4. **`plagia-postgis` (PostgreSQL 16 + PostGIS 3.4):** Almacenamiento relacional y espacial de fincas, polígonos de lotes y puntos de infestación.
5. **`plagia-minio` (MinIO Object Storage):** Repositorio compatible con S3 para ortomosaicos GeoTIFF, parches recortados y mapas renderizados.
6. **`plagia-mlflow` (MLflow Tracking Server):** Servidor centralizado de experimentos y registro de modelos.

---

## 8. Limitaciones Operativas y Gobernanza Agronómica

1. **Variabilidad lumínica y altura de vuelo en drones:** Los cambios bruscos de nubosidad o vuelos a alturas superiores a 40 metros sobre el dosel reducen la resolución espacial por píxel (GSD). Se mitiga parcialmente con el filtro **CLAHE** en preprocesamiento, pero se recomienda estandarizar vuelos entre 15 m y 25 m de altura.
2. **Similitud sintomática temprana:** En estadios iniciales, ciertas deficiencias nutricionales (ej. déficit de nitrógeno o potasio) pueden presentar clorosis visualmente similar a la roya amarilla (`yellow_rust`).
3. **Aviso de Uso Responsable (Disclaimer Agronómico Obligatorio):** Todas las respuestas de la API y la interfaz móvil incluyen explícitamente la advertencia de que **PlagIA es una herramienta de soporte a la decisión para Manejo Integrado de Plagas (MIP)** y toda aplicación química debe ser validada por un Ingeniero Agrónomo con tarjeta profesional vigente conforme a la normatividad del **ICA (Instituto Colombiano Agropecuario)**.

---

## 9. Impacto Económico y Ambiental Esperado en el Tolima

* **Reducción de entre 30% y 50% en el gasto de fungicidas e insecticidas** al pasar de fumigación total a aplicación localizada guiada por los mapas de calor GeoJSON.
* **Disminución del tiempo de inspección técnica de días a minutos** combinando el barrido aéreo con dron y la verificación puntual en terreno con la app Flutter Offline-First.
* **Trazabilidad histórica por lote y cosecha** en PostGIS, permitiendo correlacionar variedades de semilla (ej. Fedearroz 67, Fedearroz 2000) y edad fenológica con la incidencia de plagas.
