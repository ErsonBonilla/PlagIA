"""
Entrenamiento Real en GPU (NVIDIA RTX 3050 con AMP FP16) y Auditoría Neuronal
de los Modelos Fitosanitarios de PlagIA Enterprise:

1. Dominio Aéreo Dron (`01_dron_dosel_cls` - 4 clases: sano, roya_parda, roya_amarilla, suelo_desnudo).
2. Dominio Foliar de Campo (`02_campo_hoja_cls` - 10 clases fitosanitarias en español).

Registra los experimentos en MLflow, promueve el modelo al Model Registry (`@staging`),
exporta a ONNX FP32 + INT8 cuantizado y ejecuta la auditoría matemática de las neuronas.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

RAIZ_PROYECTO = Path(__file__).resolve().parents[1]
if str(RAIZ_PROYECTO) not in sys.path:
    sys.path.insert(0, str(RAIZ_PROYECTO))

import mlflow
from mlflow.tracking import MlflowClient
import torch

from ml_engine.architectures import (
    auditar_salud_neuronas,
    construir_clasificador_pytorch,
    obtener_dispositivo_computo,
)
from ml_engine.config import (
    CLASES_CAMPO_HOJA,
    CLASES_DRON,
    DIR_MODELOS,
    MLFLOW_EXPERIMENT_NAME,
    MLFLOW_MODEL_NAME,
    MLFLOW_TRACKING_URI,
    RUTA_MANIFIESTO_MULTINIVEL,
    RUTA_MANIFIESTO_PARTICIONADO,
    RUTA_METADATOS_CAMPO_MODELO,
    RUTA_METADATOS_MODELO,
    RUTA_MODELO_CAMPO_ONNX_MOVIL,
    RUTA_MODELO_CAMPO_ONNX_SERVIDOR,
    RUTA_MODELO_CAMPO_PYTORCH,
    RUTA_MODELO_ONNX_MOVIL,
    RUTA_MODELO_ONNX_SERVIDOR,
    RUTA_MODELO_PYTORCH,
    SEMILLA,
    TAMANO_LOTE,
)
from ml_engine.data_governance import (
    cargar_manifiesto_dominio_curado,
    construir_manifiesto_multinivel,
    crear_subconjunto_balanceado,
    particionar_manifiesto_agrupado,
)
from ml_engine.exporter import exportar_pytorch_a_onnx
from ml_engine.preprocessing import construir_cargadores_datos
from ml_engine.trainer import entrenar_y_registrar_mlflow


def entrenar_y_auditar_ambos_dominios() -> dict:
    dispositivo = obtener_dispositivo_computo()
    print("=" * 80)
    print(" PLAGIA ENTERPRISE - ENTRENAMIENTO GPU CUDA (AMP FP16) Y AUDITORIA NEURONAL")
    print("=" * 80)
    print(f"Dispositivo activo: {dispositivo}")
    if dispositivo.type == "cuda":
        props = torch.cuda.get_device_properties(0)
        print(f"GPU Detectada     : {props.name} ({round(props.total_memory / (1024**2), 1)} MiB VRAM)")

    mlflow.set_tracking_uri(MLFLOW_TRACKING_URI)
    mlflow.set_experiment(MLFLOW_EXPERIMENT_NAME)

    # -----------------------------------------------------------------------
    # 1. Dominio 01: Dron VANT (4 Clases Aéreas)
    # -----------------------------------------------------------------------
    print("\n[1/2] Entrenando Modelo Aéreo Dron VANT (01_dron_dosel_cls - 4 clases)...")
    df_dron_completo = cargar_manifiesto_dominio_curado("dron")
    sub_dron = crear_subconjunto_balanceado(df_dron_completo, por_clase=220, semilla=SEMILLA)
    split_dron = particionar_manifiesto_agrupado(sub_dron, semilla=SEMILLA)

    RUTA_MANIFIESTO_PARTICIONADO.parent.mkdir(parents=True, exist_ok=True)
    split_dron.to_csv(RUTA_MANIFIESTO_PARTICIONADO, index=False)
    df_multinivel = construir_manifiesto_multinivel()
    df_multinivel.to_csv(RUTA_MANIFIESTO_MULTINIVEL, index=False)

    cargadores_dron = construir_cargadores_datos(split_dron, batch_size=TAMANO_LOTE)

    resultado_dron = entrenar_y_registrar_mlflow(
        cargadores_dron["train"],
        cargadores_dron["val"],
        run_name="efficientnet_b0_dron_finetuned_cuda",
        backbone_name="efficientnet_b0",
        class_names=CLASES_DRON,
        learning_rate=4e-4,
        dropout=0.25,
        epochs=4,
        fine_tune=True,
        pretrained=True,
        tags={"dominio": "01_dron_dosel_cls", "region": "Tolima"},
        checkpoint_path=RUTA_MODELO_PYTORCH,
    )
    print(f"   -> Métricas Dron VANT: {resultado_dron['metrics']}")

    # Registrar en MLflow Model Registry y promover a @staging
    try:
        uri_modelo = f"runs:/{resultado_dron['run_id']}/model"
        reg = mlflow.register_model(model_uri=uri_modelo, name=MLFLOW_MODEL_NAME)
        MlflowClient().set_registered_model_alias(MLFLOW_MODEL_NAME, "staging", reg.version)
    except Exception as exc:
        print(f"   -> Aviso registro MLflow: {exc}")

    ckpt_dron = torch.load(RUTA_MODELO_PYTORCH, map_location="cpu", weights_only=False)
    modelo_dron = construir_clasificador_pytorch(
        backbone_name=ckpt_dron["backbone_name"],
        num_classes=len(CLASES_DRON),
        fine_tune=True,
        pretrained=False,
    )
    modelo_dron.load_state_dict(ckpt_dron["state_dict"])

    lote_x_dron, lote_y_dron = next(iter(cargadores_dron["test"]))
    auditoria_dron = auditar_salud_neuronas(modelo_dron, lote_x_dron, lote_y_dron)
    print(f"   -> Auditoría Neuronal Dron: {auditoria_dron}")

    meta_onnx_dron = exportar_pytorch_a_onnx(
        modelo_dron,
        class_names=CLASES_DRON,
        server_onnx_path=RUTA_MODELO_ONNX_SERVIDOR,
        mobile_onnx_path=RUTA_MODELO_ONNX_MOVIL,
        metadata_path=RUTA_METADATOS_MODELO,
        sync_to_flutter_assets=True,
    )
    print(
        f"   -> Exportación ONNX Dron: FP32={meta_onnx_dron['server_size_mb']} MB | "
        f"INT8 Móvil={meta_onnx_dron['mobile_size_mb']} MB (Compresión {meta_onnx_dron['compression_ratio']}x)"
    )

    # -----------------------------------------------------------------------
    # 2. Dominio 02: Patología Foliar en Campo (10 Clases Canónicas)
    # -----------------------------------------------------------------------
    print("\n[2/2] Entrenando Modelo Foliar de Campo (02_campo_hoja_cls - 10 clases)...")
    df_hoja_completo = cargar_manifiesto_dominio_curado("campo_hoja")
    sub_hoja = crear_subconjunto_balanceado(df_hoja_completo, por_clase=120, semilla=SEMILLA)
    split_hoja = particionar_manifiesto_agrupado(sub_hoja, semilla=SEMILLA)
    cargadores_hoja = construir_cargadores_datos(split_hoja, batch_size=TAMANO_LOTE)

    resultado_hoja = entrenar_y_registrar_mlflow(
        cargadores_hoja["train"],
        cargadores_hoja["val"],
        run_name="efficientnet_b0_campo_hoja_10clases_cuda",
        backbone_name="efficientnet_b0",
        class_names=CLASES_CAMPO_HOJA,
        learning_rate=4e-4,
        dropout=0.25,
        epochs=4,
        fine_tune=True,
        pretrained=True,
        tags={"dominio": "02_campo_hoja_cls", "region": "Tolima"},
        checkpoint_path=RUTA_MODELO_CAMPO_PYTORCH,
    )
    print(f"   -> Métricas Campo Hoja (10 clases): {resultado_hoja['metrics']}")

    ckpt_hoja = torch.load(RUTA_MODELO_CAMPO_PYTORCH, map_location="cpu", weights_only=False)
    modelo_hoja = construir_clasificador_pytorch(
        backbone_name=ckpt_hoja["backbone_name"],
        num_classes=len(CLASES_CAMPO_HOJA),
        fine_tune=True,
        pretrained=False,
    )
    modelo_hoja.load_state_dict(ckpt_hoja["state_dict"])

    lote_x_hoja, lote_y_hoja = next(iter(cargadores_hoja["test"]))
    auditoria_hoja = auditar_salud_neuronas(modelo_hoja, lote_x_hoja, lote_y_hoja)
    print(f"   -> Auditoría Neuronal Campo Hoja: {auditoria_hoja}")

    meta_onnx_hoja = exportar_pytorch_a_onnx(
        modelo_hoja,
        class_names=CLASES_CAMPO_HOJA,
        server_onnx_path=RUTA_MODELO_CAMPO_ONNX_SERVIDOR,
        mobile_onnx_path=RUTA_MODELO_CAMPO_ONNX_MOVIL,
        metadata_path=RUTA_METADATOS_CAMPO_MODELO,
        sync_to_flutter_assets=False,
    )
    print(
        f"   -> Exportación ONNX Campo Hoja: FP32={meta_onnx_hoja['server_size_mb']} MB | "
        f"INT8 Móvil={meta_onnx_hoja['mobile_size_mb']} MB (Compresión {meta_onnx_hoja['compression_ratio']}x)"
    )

    resumen_auditoria = {
        "dispositivo_entrenamiento": str(dispositivo),
        "modelo_dron_4_clases": {
            "run_id": resultado_dron["run_id"],
            "metricas_validacion": resultado_dron["metrics"],
            "auditoria_neuronal": auditoria_dron,
            "onnx_fp32_mb": meta_onnx_dron["server_size_mb"],
            "onnx_int8_mb": meta_onnx_dron["mobile_size_mb"],
            "factor_compresion": meta_onnx_dron["compression_ratio"],
        },
        "modelo_campo_hoja_10_clases": {
            "run_id": resultado_hoja["run_id"],
            "metricas_validacion": resultado_hoja["metrics"],
            "auditoria_neuronal": auditoria_hoja,
            "onnx_fp32_mb": meta_onnx_hoja["server_size_mb"],
            "onnx_int8_mb": meta_onnx_hoja["mobile_size_mb"],
            "factor_compresion": meta_onnx_hoja["compression_ratio"],
        },
    }
    ruta_auditoria = DIR_MODELOS / "auditoria_neuronal.json"
    ruta_auditoria.write_text(
        json.dumps(resumen_auditoria, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    print("=" * 80)
    print(f" Reporte de auditoría neuronal guardado en: {ruta_auditoria}")
    print("=" * 80)
    return resumen_auditoria


if __name__ == "__main__":
    entrenar_y_auditar_ambos_dominios()
