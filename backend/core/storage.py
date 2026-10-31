"""
Servicio de Almacenamiento de Objetos Empresarial (MinIO S3 + Fallback Local).

Guarda ortomosaicos GeoTIFF, imágenes enviadas desde campo y mapas de calor generados.
"""

from __future__ import annotations

import io
from pathlib import Path

from backend.core.config import settings


class ObjectStorageService:
    def __init__(self) -> None:
        self.local_root: Path = settings.storage_local_dir
        self.local_root.mkdir(parents=True, exist_ok=True)
        self.bucket = settings.minio_bucket
        self.minio_client = None
        self.minio_active = False

    def try_connect_minio(self) -> bool:
        try:
            from minio import Minio

            client = Minio(
                settings.minio_endpoint,
                access_key=settings.minio_access_key,
                secret_key=settings.minio_secret_key,
                secure=settings.minio_secure,
            )
            if not client.bucket_exists(self.bucket):
                client.make_bucket(self.bucket)
            self.minio_client = client
            self.minio_active = True
            return True
        except Exception:
            self.minio_active = False
            return False

    def save_bytes(self, object_key: str, data: bytes, content_type: str = "application/octet-stream") -> dict:
        """Guarda un objeto en MinIO (si está activo) y mantiene réplica en `storage_local/`."""
        local_path = self.local_root / object_key
        local_path.parent.mkdir(parents=True, exist_ok=True)
        local_path.write_bytes(data)

        storage_backend = "local_filesystem"
        if self.minio_active and self.minio_client is not None:
            try:
                self.minio_client.put_object(
                    self.bucket,
                    object_key,
                    io.BytesIO(data),
                    length=len(data),
                    content_type=content_type,
                )
                storage_backend = f"minio://{self.bucket}/{object_key}"
            except Exception:
                storage_backend = "local_filesystem"

        return {
            "object_key": object_key,
            "local_path": str(local_path),
            "storage_backend": storage_backend,
            "size_bytes": len(data),
        }


storage_service = ObjectStorageService()
