"""
Exportación Empresarial de Modelos PyTorch a ONNX (Servidor FP32 + Cuantización
Dinámica INT8 para Flutter Mobile Edge-AI) y Benchmark de Latencia GPU/CPU.

Soluciona la limitación de rutas no-ASCII de `onnxruntime.quantization` en Windows
ejecutando la cuantización dinámica sobre un directorio temporal ASCII y copiando el
artefacto cuantizado (reducción ~75% de peso) hacia `models/` y `mobile/assets/models/`.
"""

from __future__ import annotations

import json
import shutil
import tempfile
import time
from pathlib import Path

import numpy as np
import onnx
import onnxruntime as ort
import torch
import torch.nn as nn

from engine.architectures import construir_clasificador_pytorch
from engine.config import (
    AVISO_AGRONOMICO,
    CANALES_IMAGEN,
    CATALOGO_AGRONOMICO,
    CLASES_CAMPO_HOJA,
    CLASES_DRON,
    DIR_ASSETS_MOVIL,
    DIR_MODELOS,
    RUTA_METADATOS_MODELO,
    RUTA_MODELO_ONNX_MOVIL,
    RUTA_MODELO_ONNX_SERVIDOR,
    RUTA_MODELO_PYTORCH,
    TAMANO_IMAGEN,
    normalizar_etiqueta_espanol,
)


def exportar_pytorch_a_onnx(
    model: nn.Module,
    class_names: list[str] = CLASES_DRON,
    server_onnx_path: Path = RUTA_MODELO_ONNX_SERVIDOR,
    mobile_onnx_path: Path = RUTA_MODELO_ONNX_MOVIL,
    metadata_path: Path = RUTA_METADATOS_MODELO,
    sync_to_flutter_assets: bool = True,
) -> dict:
    """Exporta un modelo PyTorch a ONNX FP32 y genera la variante cuantizada INT8 real."""
    DIR_MODELOS.mkdir(parents=True, exist_ok=True)
    server_onnx_path.parent.mkdir(parents=True, exist_ok=True)

    clases_es = [normalizar_etiqueta_espanol(c) for c in class_names]
    modelo_cpu = model.to("cpu").eval()
    entrada_ficticia = torch.randn(1, CANALES_IMAGEN, *TAMANO_IMAGEN, dtype=torch.float32)

    # Exportar e inferir cuantización en un directorio temporal ASCII para evitar el fallo
    # de C++ de ONNX Runtime en rutas de Windows con tildes (ej. 'Programación').
    with tempfile.TemporaryDirectory(prefix="plagia_onnx_") as tmp_dir_str:
        tmp_dir = Path(tmp_dir_str)
        tmp_fp32 = tmp_dir / "model_fp32.onnx"
        tmp_int8 = tmp_dir / "model_int8.onnx"

        torch.onnx.export(
            modelo_cpu,
            entrada_ficticia,
            str(tmp_fp32),
            export_params=True,
            opset_version=17,
            do_constant_folding=True,
            input_names=["input"],
            output_names=["logits"],
            dynamic_axes={"input": {0: "batch_size"}, "logits": {0: "batch_size"}},
            dynamo=False,
        )

        modelo_onnx = onnx.load(str(tmp_fp32))
        onnx.checker.check_model(modelo_onnx)
        shutil.copyfile(tmp_fp32, server_onnx_path)

        from onnxruntime.quantization import QuantType, quantize_dynamic

        quantize_dynamic(
            model_input=str(tmp_fp32),
            model_output=str(tmp_int8),
            weight_type=QuantType.QUInt8,
        )
        shutil.copyfile(tmp_int8, mobile_onnx_path)

    peso_servidor_mb = round(server_onnx_path.stat().st_size / (1024 * 1024), 3)
    peso_movil_mb = round(mobile_onnx_path.stat().st_size / (1024 * 1024), 3)

    todas_clases_catalogo = list(dict.fromkeys(clases_es + CLASES_CAMPO_HOJA + ["barrenador_tallo"]))
    catalogo_completo = {
        nombre_cls: CATALOGO_AGRONOMICO.get(nombre_cls, CATALOGO_AGRONOMICO["sano"])
        for nombre_cls in todas_clases_catalogo
    }

    metadatos = {
        "model_version": "1.0.0-enterprise",
        "input_shape": [1, CANALES_IMAGEN, *TAMANO_IMAGEN],
        "classes": clases_es,
        "server_onnx_path": str(server_onnx_path.name),
        "mobile_onnx_path": str(mobile_onnx_path.name),
        "server_size_mb": peso_servidor_mb,
        "mobile_size_mb": peso_movil_mb,
        "compression_ratio": round(peso_servidor_mb / max(peso_movil_mb, 0.001), 2),
        "agronomic_catalog": catalogo_completo,
        "disclaimer": AVISO_AGRONOMICO,
    }
    metadata_path.write_text(
        json.dumps(metadatos, indent=2, ensure_ascii=False), encoding="utf-8"
    )

    if sync_to_flutter_assets:
        DIR_ASSETS_MOVIL.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(mobile_onnx_path, DIR_ASSETS_MOVIL / mobile_onnx_path.name)
        ruta_labels_tolima = DIR_ASSETS_MOVIL / "labels_tolima.json"
        ruta_labels_tolima.write_text(
            json.dumps(metadatos, indent=2, ensure_ascii=False), encoding="utf-8"
        )

    return metadatos


def asegurar_artefactos_por_defecto(class_names: list[str] = CLASES_DRON) -> dict:
    """Garantiza que existan artefactos PyTorch y ONNX (FP32 e INT8 cuantizado) con clases en español."""
    clases_es = [normalizar_etiqueta_espanol(c) for c in class_names]
    if (
        RUTA_MODELO_ONNX_SERVIDOR.exists()
        and RUTA_MODELO_ONNX_MOVIL.exists()
        and RUTA_METADATOS_MODELO.exists()
    ):
        meta_actual = json.loads(RUTA_METADATOS_MODELO.read_text(encoding="utf-8"))
        if (
            meta_actual.get("classes") == clases_es
            and meta_actual.get("mobile_size_mb", 99.0) < meta_actual.get("server_size_mb", 0.0)
        ):
            return meta_actual

    if RUTA_MODELO_PYTORCH.exists():
        ckpt = torch.load(RUTA_MODELO_PYTORCH, map_location="cpu", weights_only=False)
        backbone = ckpt.get("backbone_name", "efficientnet_b0")
        clases_guardadas = [
            normalizar_etiqueta_espanol(c) for c in ckpt.get("class_names", clases_es)
        ]
        modelo = construir_clasificador_pytorch(
            backbone_name=backbone,
            num_classes=len(clases_guardadas),
            pretrained=False,
        )
        modelo.load_state_dict(ckpt["state_dict"], strict=False)
        return exportar_pytorch_a_onnx(modelo, class_names=clases_guardadas)

    modelo = construir_clasificador_pytorch(
        backbone_name="efficientnet_b0",
        num_classes=len(clases_es),
        pretrained=True,
    )
    DIR_MODELOS.mkdir(parents=True, exist_ok=True)
    torch.save(
        {
            "state_dict": modelo.state_dict(),
            "backbone_name": "efficientnet_b0",
            "class_names": clases_es,
            "fine_tune": False,
            "dropout": 0.3,
        },
        RUTA_MODELO_PYTORCH,
    )
    return exportar_pytorch_a_onnx(modelo, class_names=clases_es)


def comparar_latencia_pytorch_vs_onnx(
    model: nn.Module,
    onnx_path: Path = RUTA_MODELO_ONNX_SERVIDOR,
    num_runs: int = 20,
) -> dict:
    """Compara la latencia media de inferencia (ms) entre PyTorch y ONNX Runtime."""
    muestra = np.random.randn(1, CANALES_IMAGEN, *TAMANO_IMAGEN).astype(np.float32)
    muestra_t = torch.from_numpy(muestra)

    modelo_cpu = model.to("cpu").eval()
    with torch.no_grad():
        _ = modelo_cpu(muestra_t)
        t0 = time.perf_counter()
        for _ in range(num_runs):
            _ = modelo_cpu(muestra_t)
        pytorch_ms = ((time.perf_counter() - t0) / num_runs) * 1000.0

    disponibles = ort.get_available_providers()
    preferidos = [p for p in ["CUDAExecutionProvider", "CPUExecutionProvider"] if p in disponibles]
    sesion = ort.InferenceSession(str(onnx_path), providers=preferidos or ["CPUExecutionProvider"])
    nombre_entrada = sesion.get_inputs()[0].name
    _ = sesion.run(None, {nombre_entrada: muestra})

    t1 = time.perf_counter()
    for _ in range(num_runs):
        _ = sesion.run(None, {nombre_entrada: muestra})
    onnx_ms = ((time.perf_counter() - t1) / num_runs) * 1000.0

    factor_aceleracion = round(pytorch_ms / max(onnx_ms, 1e-6), 2)
    return {
        "pytorch_avg_ms": round(pytorch_ms, 2),
        "onnx_avg_ms": round(onnx_ms, 2),
        "speedup_factor": factor_aceleracion,
        "onnx_active_provider": sesion.get_providers()[0],
    }


# Alias de compatibilidad
export_pytorch_to_onnx = exportar_pytorch_a_onnx
ensure_default_artifacts_exist = asegurar_artefactos_por_defecto
benchmark_pytorch_vs_onnx = comparar_latencia_pytorch_vs_onnx
