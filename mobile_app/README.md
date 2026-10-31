# PlagIA Mobile - Aplicación Empresarial Offline-First (Flutter / Dart)

Aplicación móvil multiplataforma (Android / iOS) diseñada para operar en los lotes arroceros del **Tolima** bajo condiciones de conectividad limitada o nula.

## Características Principales

1. **Inferencia Local en el Borde (Edge-AI ONNX INT8):**
   * Carga el catálogo fitosanitario y el modelo cuantizado en `assets/models/` (`labels_tolima.json` y `plagia_mobile_int8.onnx`).
   * Ejecuta diagnósticos en terreno sin conexión a internet y entrega recomendaciones de **Manejo Integrado de Plagas (MIP)**.
2. **Geolocalización GPS Nativa:**
   * Registra las coordenadas exactas (`EPSG:4326`) de cada planta/hoja evaluada en los distritos de riego del Tolima (*El Espinal, Saldaña, Guamo, Purificación, Ibagué*).
3. **Cola de Sincronización Rural (`OfflineSyncService`):**
   * Almacena las inspecciones recolectadas en campo y las sincroniza en bloque hacia `POST /api/v1/sync/batch` cuando el dispositivo detecta conexión con el backend FastAPI (`http://10.0.2.2:8000/api/v1` desde el emulador de Android Studio).
4. **Visor de Mapa de Calor Fitosanitario (`FarmHeatmapScreen`):**
   * Visualiza la cuadrícula geoespacial del lote diferenciando áreas saludables (verde), alerta moderada (naranja) y focos críticos (rojo).
