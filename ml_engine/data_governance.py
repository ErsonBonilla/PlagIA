"""
Gobernanza de Datos, Manifiesto Multinivel (Dron + Móvil) y Prevención de Fuga de Datos.

Aplica la Regla de Oro:
- Todas las clases fitosanitarias internas, funciones de negocio y particiones curadas
  están en español (`sano`, `roya_parda`, `roya_amarilla`, `suelo_desnudo`, `piricularia`, etc.).
- Las interfaces hacia librerías externas (PySpark `SparkSession`, columnas `split` para
  DataLoaders) conservan sus identificadores de protocolo.
"""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

import numpy as np
import pandas as pd

from ml_engine.config import (
    CLASES_DRON,
    CLASES_MULTINIVEL,
    DIR_CURADO_CAMPO_HOJA,
    DIR_CURADO_DRON,
    DIR_DATASET_DRON,
    DIR_DATASET_PLAGAS,
    DIR_PADDY_DOCTOR,
    PROPORCIONES_PARTICION,
    RUTA_REPORTE_CURADURIA,
    SEMILLA,
    ZONAS_ARROCERAS_TOLIMA,
)

PATRON_AUMENTADO = re.compile(r"^augmented__(\d+)_(\d+)", re.IGNORECASE)
PATRON_COPIA = re.compile(r"\s*-\s*copy", re.IGNORECASE)

MAPEO_CARPETA_DRON_A_ESPANOL = {
    "healthy": "sano",
    "brown_rust": "roya_parda",
    "yellow_rust": "roya_amarilla",
    "ground": "suelo_desnudo",
}


def _extraer_id_grupo(
    nombre_archivo: str, etiqueta_es: str, nivel_captura: str, grupo_extra: str = ""
) -> str:
    """Extrae un identificador de agrupación para impedir fuga de datos entre particiones."""
    nombre_limpio = PATRON_COPIA.sub("", Path(nombre_archivo).stem)
    coincidencia = PATRON_AUMENTADO.match(nombre_limpio)
    if coincidencia:
        id_captura = coincidencia.group(1)
        num_aug = int(coincidencia.group(2))
        bloque = num_aug // 25
        return f"{nivel_captura}_{etiqueta_es}_cap{id_captura}_b{bloque}"
    if grupo_extra:
        return f"{nivel_captura}_{etiqueta_es}_{grupo_extra}"
    return f"{nivel_captura}_{etiqueta_es}_{nombre_limpio}"


def _asignar_coordenadas_tolima(
    clave_fila: str, codigo_zona: str = "EL_ESPINAL"
) -> tuple[float, float, str]:
    """Asigna coordenadas deterministas dentro del polígono de un distrito arrocero del Tolima."""
    zonas = list(ZONAS_ARROCERAS_TOLIMA.keys())
    resumen = hashlib.md5(clave_fila.encode("utf-8")).hexdigest()
    if not codigo_zona or codigo_zona not in ZONAS_ARROCERAS_TOLIMA:
        codigo_zona = zonas[int(resumen[:2], 16) % len(zonas)]
    zona = ZONAS_ARROCERAS_TOLIMA[codigo_zona]
    min_lon, min_lat, max_lon, max_lat = zona["bbox"]
    u = int(resumen[2:10], 16) / 0xFFFFFFFF
    v = int(resumen[10:18], 16) / 0xFFFFFFFF
    lat = round(min_lat + u * (max_lat - min_lat), 6)
    lon = round(min_lon + v * (max_lon - min_lon), 6)
    return lat, lon, zona["municipio"]


def construir_manifiesto_dron(
    dir_dron: Path = DIR_CURADO_DRON, excluir_copias: bool = True
) -> pd.DataFrame:
    """Construye o carga el manifiesto para el dominio aéreo de Dron VANT (`01_dron_dosel_cls`)."""
    csv_curado = dir_dron / "manifiesto_dron_curado.csv"
    if csv_curado.exists() and excluir_copias:
        return pd.read_csv(csv_curado)

    filas: list[dict] = []
    if not dir_dron.exists():
        raise FileNotFoundError(f"No se encontró el dataset de dron en: {dir_dron}")

    for particion_dir in ["entrenamiento", "validacion", "prueba", "Train", "Test"]:
        for etiqueta_es in CLASES_DRON:
            indice_clase = CLASES_DRON.index(etiqueta_es)
            carpeta = dir_dron / particion_dir / etiqueta_es
            if not carpeta.exists():
                continue
            for ruta_img in sorted(carpeta.iterdir()):
                if not ruta_img.is_file() or ruta_img.suffix.lower() not in {".jpg", ".jpeg", ".png"}:
                    continue
                es_copia_duplicada = bool(PATRON_COPIA.search(ruta_img.stem))
                if excluir_copias and es_copia_duplicada:
                    continue
                lat, lon, municipio = _asignar_coordenadas_tolima(str(ruta_img))
                filas.append(
                    {
                        "path": str(ruta_img.resolve()),
                        "filename": ruta_img.name,
                        "label": indice_clase,
                        "label_name": etiqueta_es,
                        "source_level": "DRON_VANT",
                        "origin_split": particion_dir.lower(),
                        "is_duplicate_copy": es_copia_duplicada,
                        "group_id": _extraer_id_grupo(ruta_img.name, etiqueta_es, "dron"),
                        "rice_variety": "Fedearroz_67",
                        "crop_age_days": 60,
                        "latitude": lat,
                        "longitude": lon,
                        "municipio": municipio,
                    }
                )
    df = pd.DataFrame(filas)
    if df.empty:
        raise FileNotFoundError(f"No se hallaron imágenes válidas en {dir_dron}")
    return df


def construir_manifiesto_multinivel(
    dir_dron: Path = DIR_CURADO_DRON,
    dir_paddy: Path = DIR_CURADO_CAMPO_HOJA,
    dir_plagas: Path = DIR_DATASET_PLAGAS,
    incluir_datasets_moviles: bool = True,
    max_por_clase_movil: int = 400,
    excluir_copias: bool = True,
) -> pd.DataFrame:
    """Construye el manifiesto empresarial multinivel desde los dominios curados en `dataset/`."""
    partes: list[pd.DataFrame] = []
    df_dron = cargar_manifiesto_dominio_curado("dron")
    partes.append(df_dron)

    if incluir_datasets_moviles:
        df_hoja = cargar_manifiesto_dominio_curado("campo_hoja")
        muestras_hoja = (
            df_hoja.groupby("label_name", group_keys=False)
            .apply(lambda g: g.head(max_por_clase_movil))
            .reset_index(drop=True)
        )
        partes.append(muestras_hoja)

    return pd.concat(partes, ignore_index=True)


def auditar_fuga_datos(dir_dron: Path = DIR_DATASET_DRON) -> dict:
    """Devuelve la auditoría de integridad y verificación de cero fuga en el dominio de dron."""
    if RUTA_REPORTE_CURADURIA.exists():
        reporte = json.loads(RUTA_REPORTE_CURADURIA.read_text(encoding="utf-8"))
        if "auditoria_origen_dron" in reporte:
            return reporte["auditoria_origen_dron"]

    df_crudo = construir_manifiesto_dron(dir_dron=dir_dron, excluir_copias=False)
    copias_duplicadas = df_crudo[df_crudo["is_duplicate_copy"]]

    def _captura_base(nombre: str) -> str:
        coincidencia = PATRON_AUMENTADO.match(nombre)
        return f"fuente_aumentada_{coincidencia.group(1)}" if coincidencia else "no_aumentada"

    df_crudo["capture_source"] = df_crudo["filename"].apply(_captura_base)
    df_aug = df_crudo[df_crudo["capture_source"] != "no_aumentada"]

    cruce_particion = (
        df_aug.groupby(["label_name", "capture_source"])["origin_split"]
        .nunique()
        .reset_index()
    )
    fuentes_con_fuga = cruce_particion[cruce_particion["origin_split"] > 1]

    particiones_grupo = df_crudo.groupby("group_id")["origin_split"].nunique()
    grupos_con_fuga = particiones_grupo[particiones_grupo > 1]

    return {
        "total_raw_files": int(len(df_crudo)),
        "duplicate_copy_files_count": int(len(copias_duplicadas)),
        "duplicate_copy_examples": copias_duplicadas["filename"].head(5).tolist(),
        "augmented_files_count": int(len(df_aug)),
        "cross_split_capture_sources": int(len(fuentes_con_fuga)),
        "cross_split_groups_count": int(len(grupos_con_fuga)),
        "leaked_group_examples": grupos_con_fuga.index[:5].tolist(),
    }


def construir_manifiesto_spark(dir_dron: Path = DIR_CURADO_DRON):
    """Construye el manifiesto usando Apache Spark (PySpark) sobre `01_dron_dosel_cls`."""
    from pyspark.sql import SparkSession
    from pyspark.sql import functions as F

    spark = (
        SparkSession.builder.appName("PlagIA_Gobernanza_Datos")
        .config("spark.driver.memory", "2g")
        .getOrCreate()
    )

    dfs = []
    for particion in ["entrenamiento", "validacion", "prueba"]:
        for indice_clase, etiqueta_es in enumerate(CLASES_DRON):
            carpeta = str(Path(dir_dron) / particion / etiqueta_es)
            df = (
                spark.read.format("binaryFile")
                .option("pathGlobFilter", "*.jpg")
                .load(carpeta)
                .select(
                    F.col("path"),
                    F.element_at(F.split(F.col("path"), "/"), -1).alias("filename"),
                    F.lit(indice_clase).alias("label"),
                    F.lit(etiqueta_es).alias("label_name"),
                    F.lit("DRON_VANT").alias("source_level"),
                    F.lit(particion).alias("origin_split"),
                    F.col("length").alias("file_size_bytes"),
                )
            )
            dfs.append(df)

    manifiesto_sdf = dfs[0]
    for d in dfs[1:]:
        manifiesto_sdf = manifiesto_sdf.unionByName(d)
    return manifiesto_sdf


def crear_subconjunto_balanceado(
    manifiesto: pd.DataFrame, por_clase: int = 300, semilla: int = SEMILLA
) -> pd.DataFrame:
    """Crea un subconjunto balanceado muestreando por `group_id` para preservar integridad."""
    generador = np.random.RandomState(semilla)
    partes = []

    for indice_clase in sorted(manifiesto["label"].unique()):
        df_clase = manifiesto[manifiesto["label"] == indice_clase]
        grupos = df_clase["group_id"].unique().to_numpy(dtype=object, copy=True)
        generador.shuffle(grupos)

        elegidos = []
        conteo = 0
        for gid in grupos:
            if conteo >= por_clase:
                break
            filas_g = df_clase[df_clase["group_id"] == gid]
            elegidos.append(filas_g)
            conteo += len(filas_g)

        combinado = pd.concat(elegidos, ignore_index=True)
        if len(combinado) > por_clase:
            combinado = combinado.sample(n=por_clase, random_state=semilla)
        partes.append(combinado)

    return pd.concat(partes, ignore_index=True).sample(frac=1.0, random_state=semilla).reset_index(drop=True)


def particionar_manifiesto_agrupado(
    manifiesto: pd.DataFrame, proporciones: dict = PROPORCIONES_PARTICION, semilla: int = SEMILLA
) -> pd.DataFrame:
    """Divide el manifiesto en 70% train / 15% val / 15% test agrupando estrictamente por `group_id`."""
    generador = np.random.RandomState(semilla)
    df = manifiesto.copy()
    df["split"] = ""
    df["particion"] = ""

    for indice_clase in sorted(df["label"].unique()):
        df_clase = df[df["label"] == indice_clase]
        grupos = df_clase["group_id"].unique().to_numpy(dtype=object, copy=True)
        generador.shuffle(grupos)

        n = len(grupos)
        n_train = max(1, int(n * proporciones["train"]))
        n_val = max(1, int(n * proporciones["val"]))

        grupos_train = set(grupos[:n_train])
        grupos_val = set(grupos[n_train : n_train + n_val])
        grupos_test = set(grupos[n_train + n_val :])
        if not grupos_test and len(grupos_val) > 1:
            grupos_test.add(grupos_val.pop())

        mascara_train = (df["label"] == indice_clase) & (df["group_id"].isin(grupos_train))
        mascara_val = (df["label"] == indice_clase) & (df["group_id"].isin(grupos_val))
        mascara_test = (df["label"] == indice_clase) & (df["group_id"].isin(grupos_test))

        df.loc[mascara_train, "split"] = "train"
        df.loc[mascara_val, "split"] = "val"
        df.loc[mascara_test, "split"] = "test"

        df.loc[mascara_train, "particion"] = "entrenamiento"
        df.loc[mascara_val, "particion"] = "validacion"
        df.loc[mascara_test, "particion"] = "prueba"

    return df


def cargar_manifiesto_dominio_curado(dominio: str = "dron") -> pd.DataFrame:
    """Carga directamente el manifiesto curado y deduplicado por MD5 de los dominios especializados."""
    if dominio in {"dron", "drone", "01_dron_dosel_cls", "01_drone_canopy_cls"}:
        ruta_csv = DIR_CURADO_DRON / "manifiesto_dron_curado.csv"
    elif dominio in {"campo_hoja", "field_leaf", "02_campo_hoja_cls", "02_field_leaf_cls"}:
        ruta_csv = DIR_CURADO_CAMPO_HOJA / "manifiesto_campo_hoja_curado.csv"
    else:
        raise ValueError(f"Dominio no reconocido: {dominio}. Usa 'dron' o 'campo_hoja'.")

    if not ruta_csv.exists():
        raise FileNotFoundError(
            f"No existe el manifiesto curado en {ruta_csv}. Ejecuta `uv run python scripts/organize_datasets.py`."
        )
    return pd.read_csv(ruta_csv)


def obtener_resumen_curaduria() -> dict:
    """Devuelve el reporte consolidado de curaduría (`reporte_curaduria.json`)."""
    if not RUTA_REPORTE_CURADURIA.exists():
        raise FileNotFoundError(f"No existe {RUTA_REPORTE_CURADURIA}")
    return json.loads(RUTA_REPORTE_CURADURIA.read_text(encoding="utf-8"))


# Alias de compatibilidad para contratos externos
build_drone_manifest = construir_manifiesto_dron
build_multilevel_manifest = construir_manifiesto_multinivel
audit_data_leakage = auditar_fuga_datos
build_manifest_spark = construir_manifiesto_spark
make_balanced_subset = crear_subconjunto_balanceado
split_manifest_grouped = particionar_manifiesto_agrupado
load_curated_domain_manifest = cargar_manifiesto_dominio_curado
get_curation_summary = obtener_resumen_curaduria
