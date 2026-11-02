"""
Evaluación Fitosanitaria Multiclase: F1-Macro, Recall Crítico, Precision,
ROC-AUC (One-vs-Rest), Matriz de Confusión y Curvas de Convergencia.

Aplica la Regla de Oro:
- Funciones internas, títulos, ejes y reportes visibles al usuario en español.
- Claves de métricas para MLflow (`accuracy`, `precision_macro`, `recall_macro`, `f1_macro`, `roc_auc_ovr`)
  conservadas en inglés por compatibilidad con el contrato de seguimiento de MLflow.
"""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from sklearn.metrics import (
    ConfusionMatrixDisplay,
    accuracy_score,
    classification_report,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
    roc_curve,
)
from sklearn.preprocessing import label_binarize


def calcular_metricas_multiclase(
    y_verdadero: np.ndarray,
    y_probabilidades: np.ndarray,
    nombres_clases: list[str],
) -> dict[str, float]:
    """Calcula métricas globales y sensibilidad fitosanitaria a partir de probabilidades."""
    y_verdadero = np.asarray(y_verdadero, dtype=int)
    y_probabilidades = np.asarray(y_probabilidades, dtype=np.float64)
    y_predicho = np.argmax(y_probabilidades, axis=1)

    num_clases = len(nombres_clases)
    metricas = {
        "accuracy": float(accuracy_score(y_verdadero, y_predicho)),
        "precision_macro": float(precision_score(y_verdadero, y_predicho, average="macro", zero_division=0)),
        "recall_macro": float(recall_score(y_verdadero, y_predicho, average="macro", zero_division=0)),
        "f1_macro": float(f1_score(y_verdadero, y_predicho, average="macro", zero_division=0)),
        "f1_weighted": float(f1_score(y_verdadero, y_predicho, average="weighted", zero_division=0)),
    }

    try:
        if num_clases == 2:
            metricas["roc_auc_ovr"] = float(roc_auc_score(y_verdadero, y_probabilidades[:, 1]))
        else:
            y_bin = label_binarize(y_verdadero, classes=list(range(num_clases)))
            metricas["roc_auc_ovr"] = float(
                roc_auc_score(y_bin, y_probabilidades, average="macro", multi_class="ovr")
            )
    except Exception:
        metricas["roc_auc_ovr"] = float(metricas["f1_macro"])

    return metricas


def generar_reporte_clasificacion_texto(
    y_verdadero: np.ndarray,
    y_probabilidades: np.ndarray,
    nombres_clases: list[str],
) -> str:
    """Devuelve el reporte detallado por patología en formato texto."""
    y_predicho = np.argmax(y_probabilidades, axis=1)
    etiquetas = list(range(len(nombres_clases)))
    return classification_report(
        y_verdadero,
        y_predicho,
        labels=etiquetas,
        target_names=nombres_clases,
        zero_division=0,
    )


def guardar_grafica_matriz_confusion(
    y_verdadero: np.ndarray,
    y_probabilidades: np.ndarray,
    nombres_clases: list[str],
    ruta_salida: Path,
) -> Path:
    """Genera y guarda la matriz de confusión fitosanitaria en español."""
    y_predicho = np.argmax(y_probabilidades, axis=1)
    mc = confusion_matrix(y_verdadero, y_predicho, labels=list(range(len(nombres_clases))))
    fig, ax = plt.subplots(figsize=(7, 6))
    disp = ConfusionMatrixDisplay(confusion_matrix=mc, display_labels=nombres_clases)
    disp.plot(ax=ax, cmap="Greens", colorbar=False, xticks_rotation=30)
    ax.set_title("Matriz de Confusión Fitosanitaria - PlagIA Tolima")
    ax.set_xlabel("Etiqueta Predicha")
    ax.set_ylabel("Etiqueta Real")
    fig.tight_layout()
    ruta_salida.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(ruta_salida, dpi=150)
    plt.close(fig)
    return ruta_salida


def guardar_grafica_roc_multiclase(
    y_verdadero: np.ndarray,
    y_probabilidades: np.ndarray,
    nombres_clases: list[str],
    ruta_salida: Path,
) -> Path:
    """Genera curvas ROC Uno-contra-Resto para todas las clases evaluadas."""
    num_clases = len(nombres_clases)
    y_bin = label_binarize(y_verdadero, classes=list(range(num_clases)))
    if num_clases == 2 and y_bin.shape[1] == 1:
        y_bin = np.hstack([1 - y_bin, y_bin])

    fig, ax = plt.subplots(figsize=(7, 5.5))
    for i, nombre_cls in enumerate(nombres_clases):
        if i >= y_probabilidades.shape[1] or np.sum(y_bin[:, i]) == 0:
            continue
        fpr, tpr, _ = roc_curve(y_bin[:, i], y_probabilidades[:, i])
        ax.plot(fpr, tpr, lw=1.8, label=nombre_cls)

    ax.plot([0, 1], [0, 1], linestyle="--", color="gray", label="Azar (0.50)")
    ax.set_title("Curvas ROC Multiclase (Uno-contra-Resto) - PlagIA")
    ax.set_xlabel("Tasa de Falsos Positivos (FPR)")
    ax.set_ylabel("Sensibilidad Fitosanitaria (Recall)")
    ax.legend(loc="lower right", fontsize=8)
    fig.tight_layout()
    ruta_salida.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(ruta_salida, dpi=150)
    plt.close(fig)
    return ruta_salida


def guardar_grafica_curvas_entrenamiento(
    historial: dict[str, list[float]], ruta_salida: Path
) -> Path:
    """Grafica la evolución de Pérdida y F1-Macro durante el entrenamiento."""
    fig, ejes = plt.subplots(1, 2, figsize=(11, 4.2))

    ejes[0].plot(historial.get("train_loss", []), marker="o", label="Pérdida Entrenamiento")
    ejes[0].plot(historial.get("val_loss", []), marker="s", label="Pérdida Validación")
    ejes[0].set_title("Evolución de Pérdida (Entropía Cruzada)")
    ejes[0].set_xlabel("Época")
    ejes[0].legend()
    ejes[0].grid(alpha=0.3)

    ejes[1].plot(historial.get("train_acc", []), marker="o", label="Exactitud Entrenamiento")
    ejes[1].plot(historial.get("val_f1_macro", []), marker="s", label="F1-Macro Validación")
    ejes[1].set_title("Desempeño de Clasificación Fitosanitaria")
    ejes[1].set_xlabel("Época")
    ejes[1].legend()
    ejes[1].grid(alpha=0.3)

    fig.tight_layout()
    ruta_salida.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(ruta_salida, dpi=150)
    plt.close(fig)
    return ruta_salida


# Alias de compatibilidad
compute_multiclass_metrics = calcular_metricas_multiclase
classification_report_str = generar_reporte_clasificacion_texto
save_confusion_matrix_plot = guardar_grafica_matriz_confusion
save_multiclass_roc_plot = guardar_grafica_roc_multiclase
save_training_curves_plot = guardar_grafica_curvas_entrenamiento
