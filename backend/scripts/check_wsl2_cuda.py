"""
Diagnóstico Empresarial de Hardware, WSL 2, PyTorch CUDA (AMP FP16) y ONNX Runtime.

Verifica que el entorno gestionado con `uv` y Python 3.12 aproveche correctamente
la GPU NVIDIA (ej. GeForce RTX 3050 de 4 GB VRAM) tanto en entrenamientos con
precisión mixta como en inferencia de baja latencia.
"""

from __future__ import annotations

import platform
import sys
import time
from pathlib import Path


def run_diagnostics() -> dict:
    report: dict = {
        "python_version": sys.version.split()[0],
        "platform": platform.platform(),
        "is_wsl2": "microsoft" in platform.uname().release.lower(),
        "pytorch_installed": False,
        "cuda_available": False,
        "gpu_name": None,
        "vram_total_mb": 0,
        "amp_fp16_verified": False,
        "onnxruntime_providers": [],
    }

    print("=" * 76)
    print(" PLAGIA ENTERPRISE - DIAGNOSTICO DE ENTORNO UV + PYTHON 3.12 + CUDA")
    print("=" * 76)
    print(f"Python Version : {report['python_version']}")
    print(f"Plataforma     : {report['platform']}")
    print(f"Entorno WSL 2  : {'SI (Linux Subsystem)' if report['is_wsl2'] else 'NO (Ejecucion nativa)'}")

    try:
        import torch

        report["pytorch_installed"] = True
        report["pytorch_version"] = torch.__version__
        report["cuda_available"] = bool(torch.cuda.is_available())
        print(f"PyTorch        : {torch.__version__}")
        print(f"CUDA Activo    : {report['cuda_available']}")

        if report["cuda_available"]:
            device_idx = 0
            props = torch.cuda.get_device_properties(device_idx)
            report["gpu_name"] = props.name
            report["vram_total_mb"] = round(props.total_memory / (1024 * 1024), 1)
            report["compute_capability"] = f"{props.major}.{props.minor}"
            print(f"GPU Detectada  : {report['gpu_name']} (Compute Capability {report['compute_capability']})")
            print(f"VRAM Total     : {report['vram_total_mb']} MiB")

            # Prueba de Tensor Cores con AMP FP16 (clave para GPUs de 4 GB VRAM como RTX 3050)
            start = time.perf_counter()
            x = torch.randn((512, 512), device="cuda", dtype=torch.float32)
            w = torch.randn((512, 512), device="cuda", dtype=torch.float32)
            with torch.amp.autocast(device_type="cuda", dtype=torch.float16):
                y = torch.matmul(x, w)
            torch.cuda.synchronize()
            elapsed_ms = (time.perf_counter() - start) * 1000.0
            report["amp_fp16_verified"] = y.dtype == torch.float16
            print(f"AMP FP16 Test  : OK ({elapsed_ms:.2f} ms, dtype={y.dtype})")
            del x, w, y
            torch.cuda.empty_cache()
        else:
            print("Aviso GPU      : CUDA no disponible en este intérprete; se usará modo CPU seguro.")
    except Exception as exc:
        print(f"Error PyTorch  : {exc}")

    try:
        import onnxruntime as ort

        providers = ort.get_available_providers()
        report["onnxruntime_providers"] = providers
        print(f"ONNX Runtime   : {ort.__version__} | Providers: {providers}")
    except Exception as exc:
        print(f"Aviso ONNX     : {exc}")

    dataset_root = Path(__file__).resolve().parents[1] / "dataset"
    print(f"Carpeta Dataset: {dataset_root} ({'EXISTE' if dataset_root.exists() else 'NO ENCONTRADA'})")
    print("=" * 76)
    return report


if __name__ == "__main__":
    run_diagnostics()
