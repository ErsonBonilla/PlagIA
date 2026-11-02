# Gobernanza de Datos Multinivel - PlagIA Enterprise

## 1. Repositorio de Datasets (`dataset/`)

El motor `engine` consume las fuentes ubicadas en `C:\Users\erson\Documents\Programación\ISIDEAD\PlagIA\dataset`:

1. **Nivel Aéreo (VANT / Dron):**
   * Carpeta: `dataset/Rice crop diseases drone captured dataset`
   * Volumen: 3,727 imágenes distribuidas en `Train/` y `Test/` con 4 clases (`healthy`, `brown_rust`, `yellow_rust`, `ground`).
2. **Nivel Terreno (Móvil / Foliar):**
   * Carpeta: `dataset/Paddy Doctor - Paddy Disease Classification`
   * Volumen: 10,407 imágenes etiquetadas en 10 categorías fitosanitarias acompañadas de `train.csv` con metadatos de variedad de semilla (`variety`) y edad fenológica en días (`age`).
3. **Nivel Entomológico (Plagas en Cultivo):**
   * Carpeta: `dataset/pest`
   * Volumen: 991 imágenes en 9 clases de insectos plaga (incluyendo `stem_borer` / barrenador del tallo).

---

## 2. Prevención de Fuga de Datos (*Data Leakage*)

La auditoría ejecutada por `engine.data_governance.audit_data_leakage()` demuestra dos riesgos en el particionado original del dataset de drones:

1. **Copias duplicadas exactas (` - Copy.jpg`):** Archivos duplicados dentro del conjunto de entrenamiento.
2. **Aumentaciones offline cruzadas (`augmented__<capture_id>_<hash>.jpg`):** Variaciones sintéticas generadas a partir de la misma captura base aparecen tanto en `Train/` como en `Test/`.

Por ello, `engine/data_governance.py` filtra todas las copias redundantes, unifica los archivos y genera un particionado propio **70% Train / 15% Val / 15% Test** agrupado por `group_id`.
