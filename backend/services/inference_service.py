"""
Servicio Singleton de Inferencia Fitosanitaria Empresarial (ONNX Runtime GPU/CPU + PyTorch + YOLO).

Soporta inferencia dual:
- Dominio Aéreo Dron (`domain="dron"`): 4 clases (`sano`, `roya_parda`, `roya_amarilla`, `suelo_desnudo`).
- Dominio Foliar de Campo (`domain="campo_hoja"`): 10 clases fitosanitarias en español.
"""

from __future__ import annotations

import time
from pathlib import Path

import numpy as np
import onnxruntime as ort
import torch

from engine.architectures import DetectorFitosanitarioYOLO
from engine.config import (
    AVISO_AGRONOMICO,
    CATALOGO_AGRONOMICO,
    CLASES_CAMPO_HOJA,
    CLASES_DRON,
    RUTA_MODELO_CAMPO_ONNX_MOVIL,
    RUTA_MODELO_CAMPO_ONNX_SERVIDOR,
    RUTA_MODELO_ONNX_MOVIL,
    RUTA_MODELO_ONNX_SERVIDOR,
    USAR_CUDA,
    normalizar_etiqueta_espanol,
)
from engine.exporter import asegurar_artefactos_por_defecto
from engine.preprocessing import (
    cargar_y_preparar_imagen,
    evaluar_dominio_arroz_e_incertidumbre,
    preprocesar_para_inferencia,
)


def _softmax(logits: np.ndarray) -> np.ndarray:
    desplazado = logits - np.max(logits, axis=-1, keepdims=True)
    exps = np.exp(desplazado)
    return exps / np.sum(exps, axis=-1, keepdims=True)


class ServicioInferenciaEmpresarial:
    def __init__(self) -> None:
        self.sesion: ort.InferenceSession | None = None
        self.sesion_campo: ort.InferenceSession | None = None
        self.detector_yolo = DetectorFitosanitarioYOLO()
        self.nombres_clases: list[str] = list(CLASES_DRON)
        self.nombres_clases_campo: list[str] = list(CLASES_CAMPO_HOJA)
        self.version_modelo: str = "1.0.0-onnx-enterprise"
        self.proveedor_activo: str = "sin_inicializar"

    def load(self) -> None:
        if self.sesion is not None:
            return

        meta = asegurar_artefactos_por_defecto(class_names=self.nombres_clases)
        self.nombres_clases = [
            normalizar_etiqueta_espanol(c) for c in meta.get("classes", self.nombres_clases)
        ]
        self.version_modelo = meta.get("model_version", self.version_modelo)

        proveedores_disponibles = ort.get_available_providers()
        preferidos: list[str] = []
        if USAR_CUDA and "CUDAExecutionProvider" in proveedores_disponibles:
            preferidos.append("CUDAExecutionProvider")
        preferidos.append("CPUExecutionProvider")

        ruta_dron = (
            RUTA_MODELO_ONNX_SERVIDOR
            if RUTA_MODELO_ONNX_SERVIDOR.exists()
            else RUTA_MODELO_ONNX_MOVIL
        )
        self.sesion = ort.InferenceSession(str(ruta_dron), providers=preferidos)
        self.proveedor_activo = self.sesion.get_providers()[0]

        ruta_campo = (
            RUTA_MODELO_CAMPO_ONNX_SERVIDOR
            if RUTA_MODELO_CAMPO_ONNX_SERVIDOR.exists()
            else RUTA_MODELO_CAMPO_ONNX_MOVIL
        )
        if ruta_campo.exists():
            self.sesion_campo = ort.InferenceSession(str(ruta_campo), providers=preferidos)

    def is_loaded(self) -> bool:
        return self.sesion is not None

    def get_hardware_status(self) -> dict:
        cuda_ok = bool(torch.cuda.is_available())
        nombre_gpu = None
        vram_mb = 0.0
        if cuda_ok:
            props = torch.cuda.get_device_properties(0)
            nombre_gpu = props.name
            vram_mb = round(props.total_memory / (1024 * 1024), 1)
        return {
            "cuda_available": cuda_ok,
            "gpu_name": nombre_gpu,
            "vram_total_mb": vram_mb,
            "active_engine": f"ONNXRuntime ({self.proveedor_activo})",
        }

    def predict(
        self,
        image_source: bytes | Path | np.ndarray,
        lot_id: str = "LOTE-ESPINAL-01",
        latitude: float = 4.1486,
        longitude: float = -74.8830,
        source_type: str = "MOVIL_EN_LINEA",
        domain: str = "dron",
    ) -> dict:
        if self.sesion is None:
            self.load()
        assert self.sesion is not None

        usar_campo = domain in {"campo_hoja", "field_leaf"} and self.sesion_campo is not None
        sesion_activa = self.sesion_campo if usar_campo else self.sesion
        clases_activas = self.nombres_clases_campo if usar_campo else self.nombres_clases
        assert sesion_activa is not None

        t0 = time.perf_counter()
        img_rgb_cruda = cargar_y_preparar_imagen(image_source, aplicar_clahe=False)
        img_rgb = cargar_y_preparar_imagen(img_rgb_cruda, aplicar_clahe=True)
        entrada_x = preprocesar_para_inferencia(img_rgb, aplicar_clahe=False)

        nombre_entrada = sesion_activa.get_inputs()[0].name
        logits = sesion_activa.run(None, {nombre_entrada: entrada_x})[0]
        probs = _softmax(logits)[0]

        chequeo_dominio = evaluar_dominio_arroz_e_incertidumbre(img_rgb_cruda, probs)
        if chequeo_dominio["fuera_de_dominio"]:
            etiqueta_pred = "desconocido_no_arroz"
            confianza = round(1.0 - float(chequeo_dominio["entropia_normalizada"]), 4)
        else:
            idx_pred = int(np.argmax(probs))
            etiqueta_pred = normalizar_etiqueta_espanol(clases_activas[idx_pred])
            confianza = float(probs[idx_pred])

        info_kb = CATALOGO_AGRONOMICO.get(etiqueta_pred, CATALOGO_AGRONOMICO["sano"])
        sev_base = float(info_kb["severidad_base"])
        indice_severidad = round(
            sev_base * confianza
            if etiqueta_pred not in {"sano", "desconocido_no_arroz"}
            else (0.0 if etiqueta_pred == "desconocido_no_arroz" else 0.05 * (1.0 - confianza)),
            4,
        )

        cajas = (
            []
            if etiqueta_pred == "desconocido_no_arroz"
            else self.detector_yolo.localizar_lesiones(img_rgb, predicted_class=etiqueta_pred)
        )
        tiempo_ms = round((time.perf_counter() - t0) * 1000.0, 2)

        mapa_probabilidades = {
            normalizar_etiqueta_espanol(nombre_cls): round(float(probs[i]), 4)
            for i, nombre_cls in enumerate(clases_activas)
        }

        return {
            "lot_id": lot_id,
            "source_type": source_type,
            "disease_label": etiqueta_pred,
            "common_name": info_kb["nombre_comun"],
            "causal_agent": info_kb["agente_causal"],
            "confidence": round(confianza, 4),
            "severity_index": indice_severidad,
            "risk_level": info_kb["nivel_riesgo"],
            "mip_recommendation": info_kb["recomendacion_mip"],
            "probabilities": mapa_probabilidades,
            "bounding_boxes": cajas,
            "latitude": latitude,
            "longitude": longitude,
            "model_version": self.version_modelo,
            "inference_time_ms": tiempo_ms,
            "disclaimer": AVISO_AGRONOMICO,
        }


EnterpriseInferenceService = ServicioInferenciaEmpresarial
inference_service = ServicioInferenciaEmpresarial()
