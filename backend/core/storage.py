"""
Servicio de Almacenamiento de Objetos Empresarial (MinIO S3 + Respaldo Local).

Aplica la Regla de Oro:
- Clase, métodos y variables internas en español (`ServicioAlmacenamientoObjetos`,
  `intentar_conectar_minio`, `guardar_bytes`).
- Interfaz del SDK `minio` (`Minio`, `bucket_exists`, `make_bucket`, `put_object`) en inglés.
"""

from __future__ import annotations

import io
import socket
from pathlib import Path

from backend.core.config import configuracion


class ServicioAlmacenamientoObjetos:
    def __init__(self) -> None:
        self.raiz_local: Path = configuracion.storage_local_dir
        self.raiz_local.mkdir(parents=True, exist_ok=True)
        self.deposito = configuracion.minio_bucket
        self.cliente_minio = None
        self.minio_activo = False

    def intentar_conectar_minio(self) -> bool:
        try:
            partes = configuracion.minio_endpoint.split(":")
            host = partes[0]
            puerto = int(partes[1]) if len(partes) > 1 else 9000
            with socket.create_connection((host, puerto), timeout=0.4):
                pass

            from minio import Minio

            cliente = Minio(
                configuracion.minio_endpoint,
                access_key=configuracion.minio_access_key,
                secret_key=configuracion.minio_secret_key,
                secure=configuracion.minio_secure,
            )
            if not cliente.bucket_exists(self.deposito):
                cliente.make_bucket(self.deposito)
            self.cliente_minio = cliente
            self.minio_activo = True
            return True
        except Exception:
            self.minio_activo = False
            return False

    def guardar_bytes(
        self,
        clave_objeto: str,
        datos: bytes,
        tipo_contenido: str = "application/octet-stream",
    ) -> dict:
        """Guarda un objeto en MinIO (si está activo) y mantiene réplica en `storage_local/`."""
        ruta_local = self.raiz_local / clave_objeto
        ruta_local.parent.mkdir(parents=True, exist_ok=True)
        ruta_local.write_bytes(datos)

        motor_almacenamiento = "sistema_archivos_local"
        if self.minio_activo and self.cliente_minio is not None:
            try:
                self.cliente_minio.put_object(
                    self.deposito,
                    clave_objeto,
                    io.BytesIO(datos),
                    length=len(datos),
                    content_type=tipo_contenido,
                )
                motor_almacenamiento = f"minio://{self.deposito}/{clave_objeto}"
            except Exception:
                motor_almacenamiento = "sistema_archivos_local"

        return {
            "object_key": clave_objeto,
            "local_path": str(ruta_local),
            "storage_backend": motor_almacenamiento,
            "size_bytes": len(datos),
        }

    # Propiedades y alias de compatibilidad
    @property
    def minio_active(self) -> bool:
        return self.minio_activo

    try_connect_minio = intentar_conectar_minio
    save_bytes = guardar_bytes


servicio_almacenamiento = ServicioAlmacenamientoObjetos()
ObjectStorageService = ServicioAlmacenamientoObjetos
storage_service = servicio_almacenamiento
