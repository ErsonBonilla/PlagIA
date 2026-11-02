"""
Configuración tipada del Backend Empresarial de PlagIA (Pydantic Settings).

Aplica la Regla de Oro:
- Clase e instancias internas en español (`ConfiguracionEmpresarial`, `configuracion`).
- Interfaz exigida por `pydantic_settings` (`BaseSettings`, `SettingsConfigDict`, `model_config`)
  y nombres de variables de entorno mapeadas se conservan según contrato externo.
"""

from __future__ import annotations

import os
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

from engine.config import RAIZ_PROYECTO


class ConfiguracionEmpresarial(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="PLAGIA_", extra="ignore")

    env: str = "produccion"
    app_name: str = "PlagIA Empresarial - Vigilancia Fitosanitaria del Tolima"
    version: str = "1.0.0"

    secret_key: str = "plagia-tolima-clave-secreta-empresarial-2026"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 480

    # Base de datos principal: PostgreSQL + PostGIS
    database_url: str = os.environ.get(
        "PLAGIA_DATABASE_URL",
        "postgresql+psycopg2://plagia:plagia_secret@localhost:5432/plagia_geo",
    )
    # Base de datos conveniente de respaldo local: SQLite
    sqlite_fallback_url: str = os.environ.get(
        "PLAGIA_SQLITE_FALLBACK_URL",
        f"sqlite:///{(RAIZ_PROYECTO / 'runtime' / 'plagia_enterprise.db').as_posix()}",
    )

    redis_url: str = os.environ.get("PLAGIA_REDIS_URL", "redis://localhost:6379/0")
    celery_eager_fallback: bool = (
        os.environ.get("PLAGIA_CELERY_EAGER_FALLBACK", "true").lower() == "true"
    )

    minio_endpoint: str = os.environ.get("PLAGIA_MINIO_ENDPOINT", "localhost:9000")
    minio_access_key: str = os.environ.get("PLAGIA_MINIO_ACCESS_KEY", "plagia_admin")
    minio_secret_key: str = os.environ.get("PLAGIA_MINIO_SECRET_KEY", "plagia_minio_secret")
    minio_bucket: str = os.environ.get("PLAGIA_MINIO_BUCKET", "plagia-tolima-orthomosaics")
    minio_secure: bool = False

    storage_local_dir: Path = RAIZ_PROYECTO / "runtime" / "storage_local"


configuracion = ConfiguracionEmpresarial()
EnterpriseSettings = ConfiguracionEmpresarial
settings = configuracion
