"""
Pipeline de Preprocesamiento Radiométrico (OpenCV CLAHE), Aumento de Datos
(Albumentations) y Datasets de PyTorch optimizados para CUDA en WSL 2.

Aplica la Regla de Oro:
- Funciones y lógica interna en español.
- Métodos de protocolo exigidos por `torch.utils.data.Dataset` (`__len__`, `__getitem__`)
  y argumentos de librerías externas (`albumentations`, `DataLoader`) en inglés.
"""

from __future__ import annotations

from pathlib import Path

import albumentations as A
import cv2
import numpy as np
import pandas as pd
import torch
from torch.utils.data import DataLoader, Dataset

from ml_engine.config import IMAGENET_MEAN, IMAGENET_STD, TAMANO_IMAGEN, TAMANO_LOTE


def aplicar_correccion_radiometrica_clahe(
    imagen_rgb: np.ndarray, limite_contraste: float = 2.0
) -> np.ndarray:
    """Aplica ecualización adaptativa de histograma (CLAHE) sobre el canal de luminancia (LAB)."""
    lab = cv2.cvtColor(imagen_rgb, cv2.COLOR_RGB2LAB)
    canal_l, canal_a, canal_b = cv2.split(lab)
    clahe = cv2.createCLAHE(clipLimit=limite_contraste, tileGridSize=(8, 8))
    l_mejorado = clahe.apply(canal_l)
    lab_fusionado = cv2.merge((l_mejorado, canal_a, canal_b))
    return cv2.cvtColor(lab_fusionado, cv2.COLOR_LAB2RGB)


def cargar_y_preparar_imagen(
    origen_imagen: str | Path | bytes | np.ndarray,
    aplicar_clahe: bool = True,
) -> np.ndarray:
    """Decodifica una imagen desde ruta, bytes o arreglo y devuelve RGB uint8."""
    if isinstance(origen_imagen, np.ndarray):
        img_rgb = origen_imagen
    elif isinstance(origen_imagen, (str, Path)):
        bytes_crudos = Path(origen_imagen).read_bytes()
        buf = np.frombuffer(bytes_crudos, dtype=np.uint8)
        bgr = cv2.imdecode(buf, cv2.IMREAD_COLOR)
        if bgr is None:
            raise ValueError(f"No se pudo decodificar la imagen en: {origen_imagen}")
        img_rgb = cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)
    elif isinstance(origen_imagen, (bytes, bytearray)):
        buf = np.frombuffer(origen_imagen, dtype=np.uint8)
        bgr = cv2.imdecode(buf, cv2.IMREAD_COLOR)
        if bgr is None:
            raise ValueError("Los bytes recibidos no corresponden a una imagen JPEG/PNG válida.")
        img_rgb = cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)
    else:
        raise TypeError(f"Tipo de entrada no soportado: {type(origen_imagen)}")

    if aplicar_clahe:
        img_rgb = aplicar_correccion_radiometrica_clahe(img_rgb)
    return img_rgb


def obtener_transformaciones(
    particion: str = "train", tamano_img: tuple[int, int] = TAMANO_IMAGEN
) -> A.Compose:
    """Construye el pipeline de Albumentations para entrenamiento o validación/inferencia."""
    alto, ancho = tamano_img
    if particion in {"train", "entrenamiento"}:
        return A.Compose(
            [
                A.Resize(height=alto, width=ancho),
                A.HorizontalFlip(p=0.5),
                A.VerticalFlip(p=0.3),
                A.RandomRotate90(p=0.5),
                A.ColorJitter(brightness=0.15, contrast=0.15, saturation=0.15, hue=0.05, p=0.4),
                A.Normalize(mean=IMAGENET_MEAN, std=IMAGENET_STD, max_pixel_value=255.0),
            ]
        )
    return A.Compose(
        [
            A.Resize(height=alto, width=ancho),
            A.Normalize(mean=IMAGENET_MEAN, std=IMAGENET_STD, max_pixel_value=255.0),
        ]
    )


def preprocesar_para_inferencia(
    origen_imagen: str | Path | bytes | np.ndarray,
    aplicar_clahe: bool = True,
    tamano_img: tuple[int, int] = TAMANO_IMAGEN,
) -> np.ndarray:
    """Preprocesa una imagen y devuelve un tensor NumPy NCHW `(1, 3, H, W)` float32."""
    img_rgb = cargar_y_preparar_imagen(origen_imagen, aplicar_clahe=aplicar_clahe)
    transformacion = obtener_transformaciones(particion="test", tamano_img=tamano_img)
    transformada = transformacion(image=img_rgb)["image"]
    chw = np.transpose(transformada, (2, 0, 1)).astype(np.float32)
    return np.expand_dims(chw, axis=0)


def desnormalizar_tensor(tensor_chw: np.ndarray | torch.Tensor) -> np.ndarray:
    """Revierte la normalización de ImageNet para visualización en notebooks y reportes."""
    if isinstance(tensor_chw, torch.Tensor):
        arr = tensor_chw.detach().cpu().numpy()
    else:
        arr = np.asarray(tensor_chw)
    if arr.ndim == 4:
        arr = arr[0]
    hwc = np.transpose(arr, (1, 2, 0))
    media = np.array(IMAGENET_MEAN, dtype=np.float32)
    desv = np.array(IMAGENET_STD, dtype=np.float32)
    rgb = (hwc * desv + media) * 255.0
    return np.clip(rgb, 0, 255).astype(np.uint8)


class DatasetFitosanitarioPlagIA(Dataset):
    """Dataset PyTorch con corrección radiométrica CLAHE y aumento de datos Albumentations."""

    def __init__(
        self,
        df_manifiesto: pd.DataFrame,
        particion: str = "train",
        aplicar_clahe: bool = True,
        tamano_img: tuple[int, int] = TAMANO_IMAGEN,
    ) -> None:
        self.df = df_manifiesto.reset_index(drop=True)
        self.particion = particion
        self.aplicar_clahe = aplicar_clahe
        self.transformacion = obtener_transformaciones(particion=particion, tamano_img=tamano_img)

    # Métodos exigidos por el protocolo de `torch.utils.data.Dataset`
    def __len__(self) -> int:
        return len(self.df)

    def __getitem__(self, indice: int) -> tuple[torch.Tensor, torch.Tensor]:
        fila = self.df.iloc[indice]
        img_rgb = cargar_y_preparar_imagen(fila["path"], aplicar_clahe=self.aplicar_clahe)
        aumentada = self.transformacion(image=img_rgb)["image"]
        chw = np.transpose(aumentada, (2, 0, 1)).astype(np.float32)
        tensor_x = torch.from_numpy(chw)
        tensor_y = torch.tensor(int(fila["label"]), dtype=torch.long)
        return tensor_x, tensor_y


def construir_cargadores_datos(
    df_manifiesto_particionado: pd.DataFrame,
    batch_size: int = TAMANO_LOTE,
    apply_clahe: bool = True,
    num_workers: int = 0,
) -> dict[str, DataLoader]:
    """Construye los DataLoaders de train, val y test con soporte `pin_memory` para CUDA."""
    fijar_memoria = torch.cuda.is_available()
    cargadores: dict[str, DataLoader] = {}
    for nombre_split in ["train", "val", "test"]:
        subconjunto = df_manifiesto_particionado[df_manifiesto_particionado["split"] == nombre_split]
        if subconjunto.empty:
            continue
        ds = DatasetFitosanitarioPlagIA(
            subconjunto, particion=nombre_split, aplicar_clahe=apply_clahe
        )
        cargadores[nombre_split] = DataLoader(
            ds,
            batch_size=batch_size,
            shuffle=(nombre_split == "train"),
            num_workers=num_workers,
            pin_memory=fijar_memoria,
        )
    return cargadores


def evaluar_dominio_arroz_e_incertidumbre(
    imagen_rgb: np.ndarray,
    probabilidades: np.ndarray,
    umbral_confianza_minima: float = 0.36,
    umbral_varianza_minima: float = 4.0,
) -> dict:
    """Evalúa si la fotografía pertenece al dominio agrícola del arroz o debe rechazarse como 'desconocido_no_arroz'.

    Rechaza fotografías fuera de dominio cuando:
    1. La imagen carece de textura o varianza espectral (ej. imagen negra, blanca o sintética plana).
    2. La confianza máxima del modelo es inferior al umbral mínimo y presenta alta entropía de Shannon.
    """
    desv_espectral = float(np.std(imagen_rgb.astype(np.float32)))
    probs_seguras = np.clip(probabilidades.astype(np.float64), 1e-8, 1.0)
    entropia = -float(np.sum(probs_seguras * np.log(probs_seguras)))
    entropia_max = float(np.log(len(probs_seguras))) if len(probs_seguras) > 1 else 1.0
    entropia_norm = round(entropia / max(entropia_max, 1e-6), 4)
    confianza_max = float(np.max(probs_seguras))

    if desv_espectral < umbral_varianza_minima:
        return {
            "fuera_de_dominio": True,
            "motivo_rechazo": "Imagen sin textura espectral válida (varianza insuficiente).",
            "entropia_normalizada": entropia_norm,
            "desviacion_espectral": round(desv_espectral, 2),
        }

    if confianza_max < umbral_confianza_minima and entropia_norm > 0.88:
        return {
            "fuera_de_dominio": True,
            "motivo_rechazo": "Alta incertidumbre del clasificador; la imagen no coincide con patrones de arroz.",
            "entropia_normalizada": entropia_norm,
            "desviacion_espectral": round(desv_espectral, 2),
        }

    return {
        "fuera_de_dominio": False,
        "motivo_rechazo": None,
        "entropia_normalizada": entropia_norm,
        "desviacion_espectral": round(desv_espectral, 2),
    }


# Alias de compatibilidad
PlagIADataset = DatasetFitosanitarioPlagIA
apply_clahe_radiometric_correction = aplicar_correccion_radiometrica_clahe
load_and_prepare_image = cargar_y_preparar_image = cargar_y_preparar_imagen
get_transforms = obtener_transformaciones
preprocess_for_inference = preprocesar_para_inferencia
denormalize_tensor = desnormalizar_tensor
build_dataloaders = construir_cargadores_datos
