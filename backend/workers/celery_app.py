"""
Worker Asíncrono Celery + Redis para Segmentación e Inferencia de Ortomosaicos GeoTIFF.

Aplica la Regla de Oro:
- Funciones, variables, modelos ORM y estados internos en español (`ejecutar_analisis_ortomosaico`,
  `PROCESANDO`, `COMPLETADO`, `ORTO_DRON_VANT`).
- Configuración del protocolo Celery (`task_serializer`, `accept_content`, `result_serializer`,
  `timezone`, `enable_utc`, `task_always_eager`) en inglés.
"""

from __future__ import annotations

from pathlib import Path

from celery import Celery

from backend.core.config import configuracion
from backend.core.database import (
    DeteccionFitosanitariaORM,
    SesionLocal,
    TrabajoOrtomosaicoORM,
)
from backend.services.inference_service import inference_service
from engine.config import DIR_ARTEFACTOS
from engine.geospatial import (
    construir_geodataframe_mapa_calor,
    crear_ortomosaico_geotiff_muestra,
    exportar_artefactos_mapa_calor,
    seccionar_ortomosaico_en_parches,
)

celery_app = Celery(
    "plagia_worker_empresarial",
    broker=configuracion.redis_url,
    backend=configuracion.redis_url,
)
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="America/Bogota",
    enable_utc=True,
    task_always_eager=configuracion.celery_eager_fallback,
)


def ejecutar_analisis_ortomosaico(id_tarea: str, id_lote: str, ruta_archivo_str: str) -> dict:
    """Secciona un ortomosaico GeoTIFF, clasifica parches y genera el Mapa de Calor."""
    ruta_archivo = Path(ruta_archivo_str)
    if ruta_archivo.suffix.lower() not in {".tif", ".tiff"}:
        destino_tif = DIR_ARTEFACTOS / "ortomosaicos" / f"{id_tarea}.tif"
        ruta_archivo = crear_ortomosaico_geotiff_muestra(
            destino_tif,
            zone_key="EL_ESPINAL",
            source_images=[ruta_archivo] * 9,
        )

    parches = seccionar_ortomosaico_en_parches(ruta_archivo, patch_size=224)
    predicciones_parches: list[dict] = []

    with SesionLocal() as sesion:
        trabajo = (
            sesion.query(TrabajoOrtomosaicoORM)
            .filter(TrabajoOrtomosaicoORM.id_tarea == id_tarea)
            .first()
        )
        if trabajo:
            trabajo.estado = "PROCESANDO"
            sesion.commit()

        for p in parches:
            pred = inference_service.predict(
                p["image_rgb"],
                lot_id=id_lote,
                latitude=p["center_lat"],
                longitude=p["center_lon"],
                source_type="ORTO_DRON_VANT",
            )
            predicciones_parches.append(
                {
                    "patch_id": p["patch_id"],
                    "disease_label": pred["disease_label"],
                    "confidence": pred["confidence"],
                    "bbox_gps": p["bbox_gps"],
                    "latitude": p["center_lat"],
                    "longitude": p["center_lon"],
                }
            )
            sesion.add(
                DeteccionFitosanitariaORM(
                    id_registro_cliente=f"{id_tarea}-{p['patch_id']}",
                    lote_id=id_lote,
                    tipo_fuente="ORTO_DRON_VANT",
                    etiqueta_enfermedad=pred["disease_label"],
                    confianza=pred["confidence"],
                    indice_severidad=pred["severity_index"],
                    latitud=p["center_lat"],
                    longitud=p["center_lon"],
                    punto_wkt=f"POINT({p['center_lon']} {p['center_lat']})",
                    version_modelo=pred["model_version"],
                )
            )

        gdf = construir_geodataframe_mapa_calor(predicciones_parches, lot_id=id_lote)
        resumen_mapa = exportar_artefactos_mapa_calor(gdf, lot_id=id_lote)

        if trabajo:
            trabajo.estado = "COMPLETADO"
            trabajo.total_parches = resumen_mapa["total_cells"]
            trabajo.parches_infestados = resumen_mapa["infested_cells"]
            trabajo.tasa_infestacion = resumen_mapa["infection_rate"]
            trabajo.ruta_mapa_calor_geojson = resumen_mapa["geojson_path"]
            trabajo.ruta_mapa_calor_png = resumen_mapa["png_path"]
        sesion.commit()

    return resumen_mapa


@celery_app.task(name="plagia.procesar_ortomosaico")
def procesar_ortomosaico_tarea(id_tarea: str, id_lote: str, ruta_archivo_str: str) -> dict:
    return ejecutar_analisis_ortomosaico(
        id_tarea=id_tarea, id_lote=id_lote, ruta_archivo_str=ruta_archivo_str
    )


# Alias de compatibilidad
execute_orthomosaic_analysis = ejecutar_analisis_ortomosaico
process_orthomosaic_task = procesar_ortomosaico_tarea
