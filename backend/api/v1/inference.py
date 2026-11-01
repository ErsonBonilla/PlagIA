"""
Endpoints de Inferencia Visual Multinivel: Fotografía Móvil en Terreno y Ortomosaicos de Dron (/api/v1/inference).

Aplica la Regla de Oro:
- Lógica interna, modelos ORM (`DeteccionFitosanitariaORM`, `TrabajoOrtomosaicoORM`),
  estados (`PENDIENTE`, `PROCESANDO`, `COMPLETADO`) y mensajes al usuario en español.
- Rutas y esquemas del contrato HTTP/JSON en inglés.
"""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.orm import Session

from backend.core.config import configuracion
from backend.core.database import (
    DeteccionFitosanitariaORM,
    TrabajoOrtomosaicoORM,
    obtener_sesion_bd,
)
from backend.core.storage import servicio_almacenamiento
from backend.schemas.api_schemas import (
    RespuestaPrediccionCampo,
    RespuestaTrabajoOrtomosaico,
)
from backend.services.inference_service import inference_service
from backend.workers.celery_app import (
    ejecutar_analisis_ortomosaico,
    procesar_ortomosaico_tarea,
)

router = APIRouter(prefix="/inference", tags=["Inferencia IA Multinivel (Móvil & Dron)"])

TIPOS_IMAGEN_PERMITIDOS = {
    "image/jpeg",
    "image/jpg",
    "image/png",
    "image/tiff",
    "application/octet-stream",
}


@router.post("/online", response_model=RespuestaPrediccionCampo)
@router.post("/mobile", response_model=RespuestaPrediccionCampo)
async def predecir_imagen_movil_campo(
    file: UploadFile = File(
        ..., description="Fotografía foliar o de plaga capturada en terreno (JPEG/PNG)"
    ),
    lot_id: str = Form(default="LOTE-ESPINAL-01"),
    latitude: float = Form(default=4.1486),
    longitude: float = Form(default=-74.8830),
    domain: str = Form(default="dron"),
    sesion: Session = Depends(obtener_sesion_bd),
):
    if file.content_type and file.content_type.lower() not in TIPOS_IMAGEN_PERMITIDOS:
        raise HTTPException(
            status_code=400,
            detail=f"Formato de archivo no soportado: {file.content_type}. Envíe JPEG o PNG.",
        )

    bytes_crudos = await file.read()
    try:
        resultado = inference_service.predict(
            bytes_crudos,
            lot_id=lot_id,
            latitude=latitude,
            longitude=longitude,
            source_type="MOVIL_EN_LINEA",
            domain=domain,
        )
    except Exception as exc:
        raise HTTPException(
            status_code=400, detail=f"No fue posible procesar la imagen: {exc}"
        ) from exc

    clave_objeto = f"movil/{lot_id}/{uuid.uuid4().hex[:12]}_{file.filename or 'captura.jpg'}"
    servicio_almacenamiento.guardar_bytes(
        clave_objeto, bytes_crudos, tipo_contenido=file.content_type or "image/jpeg"
    )

    deteccion = DeteccionFitosanitariaORM(
        id_registro_cliente=f"EN-LINEA-{uuid.uuid4().hex[:10]}",
        lote_id=lot_id,
        tipo_fuente="MOVIL_EN_LINEA",
        etiqueta_enfermedad=resultado["disease_label"],
        confianza=resultado["confidence"],
        indice_severidad=resultado["severity_index"],
        latitud=latitude,
        longitud=longitude,
        punto_wkt=f"POINT({longitude} {latitude})",
        version_modelo=resultado["model_version"],
    )
    sesion.add(deteccion)
    sesion.commit()

    return RespuestaPrediccionCampo(**resultado)


@router.post("/orthomosaic", response_model=RespuestaTrabajoOrtomosaico)
async def enviar_ortomosaico_dron(
    file: UploadFile = File(..., description="Ortomosaico GeoTIFF o captura aérea de dron (VANT)"),
    lot_id: str = Form(default="LOTE-ESPINAL-01"),
    sesion: Session = Depends(obtener_sesion_bd),
):
    bytes_crudos = await file.read()
    if not bytes_crudos:
        raise HTTPException(status_code=400, detail="El archivo de ortomosaico está vacío.")

    id_tarea = f"ORTO-{uuid.uuid4().hex[:12].upper()}"
    ext = ".tif" if (file.filename or "").lower().endswith((".tif", ".tiff")) else ".jpg"
    clave_objeto = f"ortomosaicos/{lot_id}/{id_tarea}{ext}"
    objeto_guardado = servicio_almacenamiento.guardar_bytes(clave_objeto, bytes_crudos)

    trabajo = TrabajoOrtomosaicoORM(
        id_tarea=id_tarea,
        lote_id=lot_id,
        estado="PENDIENTE",
        clave_objeto_almacenamiento=clave_objeto,
    )
    sesion.add(trabajo)
    sesion.commit()

    if configuracion.celery_eager_fallback:
        ejecutar_analisis_ortomosaico(id_tarea, lot_id, objeto_guardado["local_path"])
    else:
        try:
            procesar_ortomosaico_tarea.delay(id_tarea, lot_id, objeto_guardado["local_path"])
        except Exception:
            ejecutar_analisis_ortomosaico(id_tarea, lot_id, objeto_guardado["local_path"])

    sesion.refresh(trabajo)
    return RespuestaTrabajoOrtomosaico(
        task_id=trabajo.id_tarea,
        lot_id=trabajo.lote_id,
        status=trabajo.estado,
        total_patches=trabajo.total_parches,
        infested_patches=trabajo.parches_infestados,
        infection_rate=trabajo.tasa_infestacion,
        heatmap_geojson_url=f"/api/v1/geospatial/heatmap/{lot_id}",
        message="Ortomosaico procesado y capa de calor actualizada exitosamente.",
    )


@router.get("/tasks/{task_id}", response_model=RespuestaTrabajoOrtomosaico)
def obtener_estado_trabajo_ortomosaico(
    task_id: str, sesion: Session = Depends(obtener_sesion_bd)
):
    trabajo = (
        sesion.query(TrabajoOrtomosaicoORM)
        .filter(TrabajoOrtomosaicoORM.id_tarea == task_id)
        .first()
    )
    if trabajo is None:
        raise HTTPException(status_code=404, detail=f"No existe la tarea '{task_id}'")
    return RespuestaTrabajoOrtomosaico(
        task_id=trabajo.id_tarea,
        lot_id=trabajo.lote_id,
        status=trabajo.estado,
        total_patches=trabajo.total_parches,
        infested_patches=trabajo.parches_infestados,
        infection_rate=trabajo.tasa_infestacion,
        heatmap_geojson_url=f"/api/v1/geospatial/heatmap/{trabajo.lote_id}",
        message=f"Estado de procesamiento: {trabajo.estado}",
    )
