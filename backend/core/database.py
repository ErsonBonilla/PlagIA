"""
Capa de Persistencia Geoespacial y Relacional Dual:
- Motor Principal: PostgreSQL 16 + PostGIS 3.4 (`postgresql+psycopg2://...`)
- Motor de Respaldo Conveniente: SQLite (`sqlite:///.../plagia_enterprise.db`)

Si el servidor PostgreSQL está disponible, opera sobre PostgreSQL + PostGIS;
si no está accesible en desarrollo/campo local, conmuta automáticamente a SQLite.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone

from sqlalchemy import (
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    create_engine,
    text,
)
from sqlalchemy.engine import Engine
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column, sessionmaker

from backend.core.config import settings
from ml_engine.config import ZONAS_ARROCERAS_TOLIMA


def construir_motor_bd_resiliente() -> tuple[Engine, str]:
    """Intenta conectar primero a PostgreSQL + PostGIS (principal) y hace failover limpio a SQLite."""
    url_primaria = settings.database_url
    if url_primaria.startswith("postgresql"):
        try:
            motor_pg = create_engine(
                url_primaria,
                connect_args={"connect_timeout": 2},
                pool_pre_ping=True,
                future=True,
            )
            with motor_pg.connect() as conn:
                conn.execute(text("SELECT 1"))
                try:
                    conn.execute(text("CREATE EXTENSION IF NOT EXISTS postgis"))
                    conn.commit()
                except Exception:
                    pass
            return motor_pg, "PostgreSQL/PostGIS (Principal)"
        except Exception:
            pass

    url_sqlite = (
        url_primaria if url_primaria.startswith("sqlite") else settings.sqlite_fallback_url
    )
    motor_sqlite = create_engine(
        url_sqlite,
        connect_args={"check_same_thread": False},
        future=True,
    )
    return motor_sqlite, "SQLite (Respaldo Local Activo)"


engine, ESTADO_MOTOR_BD = construir_motor_bd_resiliente()
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)


def obtener_estado_motor_bd() -> str:
    return ESTADO_MOTOR_BD


class Base(DeclarativeBase):
    pass


class FarmORM(Base):
    __tablename__ = "farms"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    name: Mapped[str] = mapped_column(String(160), nullable=False)
    municipality: Mapped[str] = mapped_column(String(80), nullable=False)
    irrigation_district: Mapped[str] = mapped_column(String(120), nullable=False)
    owner_name: Mapped[str] = mapped_column(String(140), nullable=False)
    total_area_ha: Mapped[float] = mapped_column(Float, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )


class LotORM(Base):
    __tablename__ = "lots"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    farm_id: Mapped[str] = mapped_column(String(64), ForeignKey("farms.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(140), nullable=False)
    municipality: Mapped[str] = mapped_column(String(80), nullable=False)
    rice_variety: Mapped[str] = mapped_column(String(80), nullable=False)
    crop_age_days: Mapped[int] = mapped_column(Integer, default=55)
    area_ha: Mapped[float] = mapped_column(Float, default=25.0)
    center_lat: Mapped[float] = mapped_column(Float, nullable=False)
    center_lon: Mapped[float] = mapped_column(Float, nullable=False)
    polygon_wkt: Mapped[str] = mapped_column(Text, nullable=False)
    polygon_geojson: Mapped[str] = mapped_column(Text, nullable=False)


class PhytosanitaryDetectionORM(Base):
    __tablename__ = "phytosanitary_detections"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    client_record_id: Mapped[str | None] = mapped_column(String(96), nullable=True, index=True)
    lot_id: Mapped[str] = mapped_column(String(64), index=True)
    source_type: Mapped[str] = mapped_column(String(40), default="MOVIL_EN_LINEA")
    disease_label: Mapped[str] = mapped_column(String(64), nullable=False)
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    severity_index: Mapped[float] = mapped_column(Float, nullable=False)
    latitude: Mapped[float] = mapped_column(Float, nullable=False)
    longitude: Mapped[float] = mapped_column(Float, nullable=False)
    point_wkt: Mapped[str] = mapped_column(String(120), nullable=False)
    model_version: Mapped[str] = mapped_column(String(64), default="1.0.0-enterprise")
    captured_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )


class OrthomosaicJobORM(Base):
    __tablename__ = "orthomosaic_jobs"

    task_id: Mapped[str] = mapped_column(String(96), primary_key=True)
    lot_id: Mapped[str] = mapped_column(String(64), index=True)
    status: Mapped[str] = mapped_column(String(32), default="PENDING")
    storage_object_key: Mapped[str] = mapped_column(String(255), default="")
    total_patches: Mapped[int] = mapped_column(Integer, default=0)
    infested_patches: Mapped[int] = mapped_column(Integer, default=0)
    infection_rate: Mapped[float] = mapped_column(Float, default=0.0)
    heatmap_geojson_path: Mapped[str] = mapped_column(String(255), default="")
    heatmap_png_path: Mapped[str] = mapped_column(String(255), default="")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )


def init_db_and_seed_tolima_lots() -> None:
    """Crea las tablas e inserta las fincas y lotes arroceros de referencia en el Tolima."""
    Base.metadata.create_all(bind=engine)
    with SessionLocal() as db:
        if db.query(FarmORM).count() > 0:
            return

        farms = [
            FarmORM(
                id="FINCA-TOL-01",
                name="Hacienda Arrocera San Isidro",
                municipality="El Espinal",
                irrigation_district="Usocoello",
                owner_name="Agroindustrial del Tolima S.A.S.",
                total_area_ha=120.0,
            ),
            FarmORM(
                id="FINCA-TOL-02",
                name="Agrícola Las Palmas del Saldaña",
                municipality="Saldaña",
                irrigation_district="Usosaldaña",
                owner_name="Inversiones Arroceras del Sur",
                total_area_ha=95.0,
            ),
        ]
        db.add_all(farms)

        espinal_bbox = ZONAS_ARROCERAS_TOLIMA["EL_ESPINAL"]["bbox"]
        saldana_bbox = ZONAS_ARROCERAS_TOLIMA["SALDANA"]["bbox"]

        def _bbox_to_wkt_and_geojson(bbox: tuple[float, float, float, float]) -> tuple[str, str]:
            min_lon, min_lat, max_lon, max_lat = bbox
            wkt = (
                f"POLYGON(({min_lon} {min_lat}, {max_lon} {min_lat}, "
                f"{max_lon} {max_lat}, {min_lon} {max_lat}, {min_lon} {min_lat}))"
            )
            geojson = json.dumps(
                {
                    "type": "Polygon",
                    "coordinates": [
                        [
                            [min_lon, min_lat],
                            [max_lon, min_lat],
                            [max_lon, max_lat],
                            [min_lon, max_lat],
                            [min_lon, min_lat],
                        ]
                    ],
                }
            )
            return wkt, geojson

        wkt_1, geo_1 = _bbox_to_wkt_and_geojson(espinal_bbox)
        wkt_2, geo_2 = _bbox_to_wkt_and_geojson(saldana_bbox)

        lots = [
            LotORM(
                id="LOTE-ESPINAL-01",
                farm_id="FINCA-TOL-01",
                name="Lote Las Acacias - Sector Norte",
                municipality="El Espinal",
                rice_variety="Fedearroz 67",
                crop_age_days=58,
                area_ha=42.5,
                center_lat=ZONAS_ARROCERAS_TOLIMA["EL_ESPINAL"]["center_lat"],
                center_lon=ZONAS_ARROCERAS_TOLIMA["EL_ESPINAL"]["center_lon"],
                polygon_wkt=wkt_1,
                polygon_geojson=geo_1,
            ),
            LotORM(
                id="LOTE-SALDANA-01",
                farm_id="FINCA-TOL-02",
                name="Lote El Canal - Distrito Saldaña",
                municipality="Saldaña",
                rice_variety="Fedearroz 2000",
                crop_age_days=45,
                area_ha=38.0,
                center_lat=ZONAS_ARROCERAS_TOLIMA["SALDANA"]["center_lat"],
                center_lon=ZONAS_ARROCERAS_TOLIMA["SALDANA"]["center_lon"],
                polygon_wkt=wkt_2,
                polygon_geojson=geo_2,
            ),
        ]
        db.add_all(lots)

        seed_detections = [
            PhytosanitaryDetectionORM(
                client_record_id="SEMILLA-001",
                lot_id="LOTE-ESPINAL-01",
                source_type="DRON_VANT",
                disease_label="sano",
                confidence=0.96,
                severity_index=0.02,
                latitude=4.1450,
                longitude=-74.8900,
                point_wkt="POINT(-74.8900 4.1450)",
            ),
            PhytosanitaryDetectionORM(
                client_record_id="SEMILLA-002",
                lot_id="LOTE-ESPINAL-01",
                source_type="DRON_VANT",
                disease_label="roya_parda",
                confidence=0.92,
                severity_index=0.72,
                latitude=4.1486,
                longitude=-74.8830,
                point_wkt="POINT(-74.8830 4.1486)",
            ),
            PhytosanitaryDetectionORM(
                client_record_id="SEMILLA-003",
                lot_id="LOTE-ESPINAL-01",
                source_type="MOVIL_OFFLINE",
                disease_label="roya_amarilla",
                confidence=0.89,
                severity_index=0.73,
                latitude=4.1515,
                longitude=-74.8780,
                point_wkt="POINT(-74.8780 4.1515)",
            ),
        ]
        db.add_all(seed_detections)
        db.commit()


def get_db():
    db: Session = SessionLocal()
    try:
        yield db
    finally:
        db.close()
