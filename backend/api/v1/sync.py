"""
Endpoints de Sincronización Offline-First y Actualización OTA para la App Móvil Flutter (/api/v1/sync).

Aplica la Regla de Oro:
- Lógica interna, modelo `DeteccionFitosanitariaORM` y etiquetas en español.
- Contrato JSON de sincronización conservado en inglés.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.core.database import DeteccionFitosanitariaORM, obtener_sesion_bd
from backend.schemas.api_schemas import (
    RespuestaSincronizacionLoteOffline,
    SolicitudSincronizacionLoteOffline,
)
from ml_engine.config import RUTA_METADATOS_MODELO, normalizar_etiqueta_espanol
from ml_engine.exporter import asegurar_artefactos_por_defecto

router = APIRouter(prefix="/sync", tags=["Sincronización Offline-First (Flutter Edge-AI)"])


@router.post("/batch", response_model=RespuestaSincronizacionLoteOffline)
def sincronizar_lote_registros_offline(
    carga: SolicitudSincronizacionLoteOffline,
    sesion: Session = Depends(obtener_sesion_bd),
):
    """Recibe el lote de diagnósticos recolectados sin internet por la App Flutter en el campo."""
    ids_sincronizados: list[str] = []
    lote_objetivo = "LOTE-ESPINAL-01"

    for elemento in carga.records:
        lote_objetivo = elemento.lot_id
        etiqueta_es = normalizar_etiqueta_espanol(elemento.disease_label)
        existente = (
            sesion.query(DeteccionFitosanitariaORM)
            .filter(DeteccionFitosanitariaORM.id_registro_cliente == elemento.client_record_id)
            .first()
        )
        if existente is None:
            sesion.add(
                DeteccionFitosanitariaORM(
                    id_registro_cliente=elemento.client_record_id,
                    lote_id=elemento.lot_id,
                    tipo_fuente="MOVIL_OFFLINE",
                    etiqueta_enfermedad=etiqueta_es,
                    confianza=elemento.confidence,
                    indice_severidad=elemento.severity_index,
                    latitud=elemento.latitude,
                    longitud=elemento.longitude,
                    punto_wkt=f"POINT({elemento.longitude} {elemento.latitude})",
                    version_modelo=elemento.model_version,
                    capturado_en=elemento.captured_at or datetime.now(timezone.utc),
                )
            )
        ids_sincronizados.append(elemento.client_record_id)

    sesion.commit()

    registros_lote = (
        sesion.query(DeteccionFitosanitariaORM)
        .filter(DeteccionFitosanitariaORM.lote_id == lote_objetivo)
        .all()
    )
    total = len(registros_lote)
    infestados = sum(
        1
        for r in registros_lote
        if normalizar_etiqueta_espanol(r.etiqueta_enfermedad) != "sano"
    )
    tasa_infestacion = round(infestados / max(1, total), 4)

    return RespuestaSincronizacionLoteOffline(
        device_id=carga.device_id,
        received_count=len(carga.records),
        synced_ids=ids_sincronizados,
        lot_updated_infection_rate=tasa_infestacion,
        server_timestamp=datetime.now(timezone.utc),
    )


@router.get("/mobile-model")
def obtener_manifiesto_modelo_movil():
    """Entrega el manifiesto OTA del modelo ONNX INT8 embebido para dispositivos Flutter."""
    if not RUTA_METADATOS_MODELO.exists():
        asegurar_artefactos_por_defecto()
    return json.loads(RUTA_METADATOS_MODELO.read_text(encoding="utf-8"))
