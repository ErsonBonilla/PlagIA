"""
Configuración tipada del Backend Empresarial de PlagIA (Pydantic Settings).

Establece PostgreSQL + PostGIS como base de datos principal y SQLite como
base de datos conveniente de respaldo automático (Auto-Failover).
"""

from __future__ import annotations

import os
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

from ml_engine.config import PROJECT_ROOT


class EnterpriseSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="PLAGIA_", extra="ignore")

    env: str = "production"
    app_name: str = "PlagIA Enterprise - Vigilancia Fitosanitaria Tolima"
    version: str = "1.0.0"

    secret_key: str = "plagia-tolima-enterprise-secret-key-change-in-prod-2026"
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
        f"sqlite:///{(PROJECT_ROOT / 'plagia_enterprise.db').as_posix()}",
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

    storage_local_dir: Path = PROJECT_ROOT / "storage_local"


settings = EnterpriseSettings()
