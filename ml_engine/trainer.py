"""
Entrenador Empresarial en PyTorch con Precisión Mixta Automática (AMP FP16),
Acumulación de Gradientes (calibrado para RTX 3050 4 GB VRAM) y Tracking en MLflow.

Aplica la Regla de Oro:
- Lógica, funciones y nombres de clases fitosanitarias internas en español.
- Contratos hacia `mlflow`, `torch.amp` y `torch.optim` conservados en inglés.
"""

from __future__ import annotations

import tempfile
from pathlib import Path

import mlflow
import mlflow.pytorch
import numpy as np
import torch
import torch.nn as nn
from mlflow.models import infer_signature
from sklearn.utils.class_weight import compute_class_weight
from torch.utils.data import DataLoader

from ml_engine.architectures import (
    construir_clasificador_pytorch,
    fijar_semillas_reproducibles,
    liberar_memoria_cuda,
    obtener_dispositivo_computo,
)
from ml_engine.config import (
    AMP_FP16,
    CANALES_IMAGEN,
    CLASES_DRON,
    DIR_MODELOS,
    PASOS_ACUMULACION_GRADIENTE,
    RUTA_MODELO_PYTORCH,
    SEMILLA,
    TAMANO_IMAGEN,
)
from ml_engine.evaluation import (
    calcular_metricas_multiclase,
    generar_reporte_clasificacion_texto,
    guardar_grafica_curvas_entrenamiento,
    guardar_grafica_matriz_confusion,
    guardar_grafica_roc_multiclase,
)


def calcular_pesos_clase_balanceados(
    etiquetas: list[int] | np.ndarray, num_clases: int, dispositivo: torch.device
) -> torch.Tensor:
    """Calcula pesos balanceados por clase para compensar asimetrías en el dataset."""
    y = np.asarray(etiquetas, dtype=int)
    clases_presentes = np.unique(y)
    pesos = np.ones(num_clases, dtype=np.float32)
    calculados = compute_class_weight(class_weight="balanced", classes=clases_presentes, y=y)
    for idx_cls, w in zip(clases_presentes, calculados):
        if 0 <= int(idx_cls) < num_clases:
            pesos[int(idx_cls)] = float(w)
    return torch.tensor(pesos, dtype=torch.float32, device=dispositivo)


@torch.no_grad()
def evaluar_cargador_datos(
    modelo: nn.Module,
    cargador: DataLoader,
    criterio: nn.Module,
    dispositivo: torch.device,
    nombres_clases: list[str],
) -> tuple[float, np.ndarray, np.ndarray, dict[str, float]]:
    """Evalúa un DataLoader devolviendo pérdida media, etiquetas reales, probabilidades y métricas."""
    modelo.eval()
    perdida_total = 0.0
    total_muestras = 0
    todos_objetivos: list[np.ndarray] = []
    todas_probs: list[np.ndarray] = []

    for lote_x, lote_y in cargador:
        lote_x = lote_x.to(dispositivo, non_blocking=True)
        lote_y = lote_y.to(dispositivo, non_blocking=True)
        logits = modelo(lote_x)
        perdida = criterio(logits, lote_y)
        probs = torch.softmax(logits, dim=1)

        tam = lote_x.size(0)
        perdida_total += float(perdida.item()) * tam
        total_muestras += tam
        todos_objetivos.append(lote_y.cpu().numpy())
        todas_probs.append(probs.cpu().numpy())

    y_verdadero = np.concatenate(todos_objetivos, axis=0)
    y_probs = np.concatenate(todas_probs, axis=0)
    perdida_media = perdida_total / max(1, total_muestras)
    metricas = calcular_metricas_multiclase(y_verdadero, y_probs, nombres_clases=nombres_clases)
    metricas["val_loss"] = float(perdida_media)
    return perdida_media, y_verdadero, y_probs, metricas


def entrenar_y_registrar_mlflow(
    train_loader: DataLoader,
    val_loader: DataLoader,
    run_name: str,
    backbone_name: str = "resnet50",
    class_names: list[str] = CLASES_DRON,
    learning_rate: float = 1e-3,
    dropout: float = 0.3,
    epochs: int = 3,
    fine_tune: bool = False,
    pretrained: bool = True,
    use_amp_fp16: bool = AMP_FP16,
    grad_accum_steps: int = PASOS_ACUMULACION_GRADIENTE,
    tags: dict[str, str] | None = None,
    checkpoint_path: Path = RUTA_MODELO_PYTORCH,
) -> dict:
    """Entrena una variante PyTorch y registra parámetros, métricas, gráficas y modelo en MLflow."""
    fijar_semillas_reproducibles(SEMILLA)
    dispositivo = obtener_dispositivo_computo()
    amp_activo = bool(use_amp_fp16 and dispositivo.type == "cuda")

    num_clases = len(class_names)
    modelo = construir_clasificador_pytorch(
        backbone_name=backbone_name,
        num_classes=num_clases,
        dropout=dropout,
        fine_tune=fine_tune,
        pretrained=pretrained,
    ).to(dispositivo)

    etiquetas_entrenamiento = (
        train_loader.dataset.df["label"].to_numpy()
        if hasattr(train_loader.dataset, "df")
        else np.arange(num_clases)
    )
    pesos_clase_t = calcular_pesos_clase_balanceados(
        etiquetas_entrenamiento, num_clases, dispositivo
    )
    criterio = nn.CrossEntropyLoss(weight=pesos_clase_t)

    parametros_entrenables = [p for p in modelo.parameters() if p.requires_grad]
    optimizador = torch.optim.AdamW(parametros_entrenables, lr=learning_rate, weight_decay=1e-4)
    programador_lr = torch.optim.lr_scheduler.ReduceLROnPlateau(
        optimizador, mode="max", factor=0.5, patience=1
    )
    escalador = torch.amp.GradScaler("cuda", enabled=amp_activo)

    historial: dict[str, list[float]] = {
        "train_loss": [],
        "val_loss": [],
        "train_acc": [],
        "val_f1_macro": [],
    }

    mejor_f1 = -1.0
    mejor_estado = None

    with mlflow.start_run(run_name=run_name) as corrida:
        mlflow.log_params(
            {
                "backbone": backbone_name,
                "phase": "Fase_B_Ajuste_Fino" if fine_tune else "Fase_A_Base_Congelada",
                "learning_rate": learning_rate,
                "dropout": dropout,
                "epochs": epochs,
                "batch_size": train_loader.batch_size or 16,
                "grad_accum_steps": grad_accum_steps,
                "effective_batch_size": (train_loader.batch_size or 16) * grad_accum_steps,
                "device": str(dispositivo),
                "amp_fp16": amp_activo,
                "num_classes": num_clases,
                "seed": SEMILLA,
            }
        )
        if tags:
            mlflow.set_tags(tags)

        for epoca in range(epochs):
            modelo.train()
            perdida_acumulada = 0.0
            aciertos = 0
            total = 0
            optimizador.zero_grad(set_to_none=True)

            for idx_paso, (lote_x, lote_y) in enumerate(train_loader):
                lote_x = lote_x.to(dispositivo, non_blocking=True)
                lote_y = lote_y.to(dispositivo, non_blocking=True)

                with torch.amp.autocast(
                    device_type=dispositivo.type, dtype=torch.float16, enabled=amp_activo
                ):
                    logits = modelo(lote_x)
                    perdida = criterio(logits, lote_y) / grad_accum_steps

                escalador.scale(perdida).backward()

                if (idx_paso + 1) % grad_accum_steps == 0 or (idx_paso + 1) == len(train_loader):
                    escalador.step(optimizador)
                    escalador.update()
                    optimizador.zero_grad(set_to_none=True)

                tam = lote_x.size(0)
                perdida_acumulada += float(perdida.item()) * grad_accum_steps * tam
                predicciones = torch.argmax(logits, dim=1)
                aciertos += int((predicciones == lote_y).sum().item())
                total += tam

            perdida_train = perdida_acumulada / max(1, total)
            exactitud_train = aciertos / max(1, total)
            perdida_val, y_verdadero, y_probs, metricas_val = evaluar_cargador_datos(
                modelo, val_loader, criterio, dispositivo, class_names
            )
            programador_lr.step(metricas_val["f1_macro"])

            historial["train_loss"].append(perdida_train)
            historial["val_loss"].append(perdida_val)
            historial["train_acc"].append(exactitud_train)
            historial["val_f1_macro"].append(metricas_val["f1_macro"])

            mlflow.log_metrics(
                {
                    "train_loss": perdida_train,
                    "train_accuracy": exactitud_train,
                    "val_loss": perdida_val,
                    "val_accuracy": metricas_val["accuracy"],
                    "val_f1_macro": metricas_val["f1_macro"],
                    "val_recall_macro": metricas_val["recall_macro"],
                },
                step=epoca,
            )

            if metricas_val["f1_macro"] >= mejor_f1:
                mejor_f1 = metricas_val["f1_macro"]
                mejor_estado = {k: v.detach().cpu().clone() for k, v in modelo.state_dict().items()}

        if mejor_estado is not None:
            modelo.load_state_dict(mejor_estado)

        _, y_verdadero, y_probs, metricas_finales = evaluar_cargador_datos(
            modelo, val_loader, criterio, dispositivo, class_names
        )
        mlflow.log_metrics(metricas_finales)

        dir_tmp = Path(tempfile.mkdtemp())
        ruta_mc = guardar_grafica_matriz_confusion(
            y_verdadero, y_probs, class_names, dir_tmp / "confusion_matrix.png"
        )
        ruta_roc = guardar_grafica_roc_multiclase(
            y_verdadero, y_probs, class_names, dir_tmp / "roc_curve.png"
        )
        ruta_curvas = guardar_grafica_curvas_entrenamiento(
            historial, dir_tmp / "training_curves.png"
        )
        texto_reporte = generar_reporte_clasificacion_texto(y_verdadero, y_probs, class_names)
        ruta_reporte = dir_tmp / "classification_report.txt"
        ruta_reporte.write_text(texto_reporte, encoding="utf-8")

        mlflow.log_artifact(str(ruta_mc))
        mlflow.log_artifact(str(ruta_roc))
        mlflow.log_artifact(str(ruta_curvas))
        mlflow.log_artifact(str(ruta_reporte))

        modelo_cpu = modelo.to("cpu").eval()
        muestra_entrada = np.zeros((1, CANALES_IMAGEN, *TAMANO_IMAGEN), dtype=np.float32)
        with torch.no_grad():
            muestra_salida = modelo_cpu(torch.from_numpy(muestra_entrada)).numpy()
        firma = infer_signature(muestra_entrada, muestra_salida)

        DIR_MODELOS.mkdir(parents=True, exist_ok=True)
        checkpoint_path.parent.mkdir(parents=True, exist_ok=True)
        torch.save(
            {
                "state_dict": modelo_cpu.state_dict(),
                "backbone_name": backbone_name,
                "class_names": class_names,
                "fine_tune": fine_tune,
                "dropout": dropout,
                "metrics": metricas_finales,
                "run_id": corrida.info.run_id,
            },
            checkpoint_path,
        )

        try:
            mlflow.pytorch.log_model(
                modelo_cpu,
                name="model",
                signature=firma,
                serialization_format="cloudpickle",
            )
        except Exception:
            mlflow.log_artifact(str(checkpoint_path), artifact_path="model")

        run_id = corrida.info.run_id

    del modelo, optimizador, criterio
    liberar_memoria_cuda()

    return {
        "run_id": run_id,
        "run_name": run_name,
        "metrics": metricas_finales,
        "checkpoint_path": str(checkpoint_path),
    }


# Alias de compatibilidad
compute_balanced_class_weights_tensor = calcular_pesos_clase_balanceados
evaluate_dataloader = evaluar_cargador_datos
train_and_log_mlflow = entrenar_y_registrar_mlflow
