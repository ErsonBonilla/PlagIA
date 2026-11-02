"""
Capa de Persistencia Geoespacial y Relacional Dual bajo la Regla de Oro:
- Motor Principal: PostgreSQL 16 + PostGIS 3.4 (`postgresql+psycopg2://...`)
- Motor de Respaldo Conveniente: SQLite (`sqlite:///.../plagia_enterprise.db`)

Todas las clases ORM, tablas (`fincas`, `lotes`, `detecciones_fitosanitarias`,
`trabajos_ortomosaico`), columnas y estados internos (`PENDIENTE`, `PROCESANDO`,
`COMPLETADO`) están en español. Los estándares espaciales OGC WKT (`POINT`, `POLYGON`)
y RFC 7946 GeoJSON se conservan en inglés por protocolo.
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

from backend.core.config import configuracion
from engine.config import ZONAS_ARROCERAS_TOLIMA


def construir_motor_bd_resiliente() -> tuple[Engine, str]:
    """Intenta conectar primero a PostgreSQL + PostGIS (principal) y hace failover limpio a SQLite."""
    import socket
    from urllib.parse import urlparse

    url_primaria = configuracion.database_url
    if url_primaria.startswith("postgresql"):
        try:
            parsed = urlparse(url_primaria)
            host_pg = parsed.hostname or "localhost"
            puerto_pg = parsed.port or 5432
            with socket.create_connection((host_pg, puerto_pg), timeout=0.4):
                pass

            motor_pg = create_engine(
                url_primaria,
                connect_args={"connect_timeout": 1},
                pool_pre_ping=True,
                future=True,
            )
            with motor_pg.connect() as conexion:
                conexion.execute(text("SELECT 1"))
                try:
                    conexion.execute(text("CREATE EXTENSION IF NOT EXISTS postgis"))
                    conexion.commit()
                except Exception:
                    pass
            return motor_pg, "PostgreSQL/PostGIS (Principal)"
        except Exception:
            pass

    url_sqlite = (
        url_primaria if url_primaria.startswith("sqlite") else configuracion.sqlite_fallback_url
    )
    motor_sqlite = create_engine(
        url_sqlite,
        connect_args={"check_same_thread": False},
        future=True,
    )
    return motor_sqlite, "SQLite (Respaldo Local Activo)"


motor_bd, ESTADO_MOTOR_BD = construir_motor_bd_resiliente()
SesionLocal = sessionmaker(
    bind=motor_bd, autoflush=False, autocommit=False, expire_on_commit=False
)


def obtener_estado_motor_bd() -> str:
    return ESTADO_MOTOR_BD


class BaseORM(DeclarativeBase):
    pass


class FincaORM(BaseORM):
    __tablename__ = "fincas"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    nombre: Mapped[str] = mapped_column(String(160), nullable=False)
    municipio: Mapped[str] = mapped_column(String(80), nullable=False)
    distrito_riego: Mapped[str] = mapped_column(String(120), nullable=False)
    propietario: Mapped[str] = mapped_column(String(140), nullable=False)
    area_total_ha: Mapped[float] = mapped_column(Float, nullable=False)
    creado_en: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )


class LoteORM(BaseORM):
    __tablename__ = "lotes"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    finca_id: Mapped[str] = mapped_column(String(64), ForeignKey("fincas.id"), nullable=False)
    nombre: Mapped[str] = mapped_column(String(140), nullable=False)
    municipio: Mapped[str] = mapped_column(String(80), nullable=False)
    variedad_arroz: Mapped[str] = mapped_column(String(80), nullable=False)
    edad_cultivo_dias: Mapped[int] = mapped_column(Integer, default=55)
    area_ha: Mapped[float] = mapped_column(Float, default=25.0)
    latitud_centro: Mapped[float] = mapped_column(Float, nullable=False)
    longitud_centro: Mapped[float] = mapped_column(Float, nullable=False)
    poligono_wkt: Mapped[str] = mapped_column(Text, nullable=False)
    poligono_geojson: Mapped[str] = mapped_column(Text, nullable=False)


class DeteccionFitosanitariaORM(BaseORM):
    __tablename__ = "detecciones_fitosanitarias"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    id_registro_cliente: Mapped[str | None] = mapped_column(String(96), nullable=True, index=True)
    lote_id: Mapped[str] = mapped_column(String(64), index=True)
    tipo_fuente: Mapped[str] = mapped_column(String(40), default="MOVIL_EN_LINEA")
    etiqueta_enfermedad: Mapped[str] = mapped_column(String(64), nullable=False)
    confianza: Mapped[float] = mapped_column(Float, nullable=False)
    indice_severidad: Mapped[float] = mapped_column(Float, nullable=False)
    latitud: Mapped[float] = mapped_column(Float, nullable=False)
    longitud: Mapped[float] = mapped_column(Float, nullable=False)
    punto_wkt: Mapped[str] = mapped_column(String(120), nullable=False)
    version_modelo: Mapped[str] = mapped_column(String(64), default="1.0.0-enterprise")
    capturado_en: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )


class TrabajoOrtomosaicoORM(BaseORM):
    __tablename__ = "trabajos_ortomosaico"

    id_tarea: Mapped[str] = mapped_column(String(96), primary_key=True)
    lote_id: Mapped[str] = mapped_column(String(64), index=True)
    estado: Mapped[str] = mapped_column(String(32), default="PENDIENTE")
    clave_objeto_almacenamiento: Mapped[str] = mapped_column(String(255), default="")
    total_parches: Mapped[int] = mapped_column(Integer, default=0)
    parches_infestados: Mapped[int] = mapped_column(Integer, default=0)
    tasa_infestacion: Mapped[float] = mapped_column(Float, default=0.0)
    ruta_mapa_calor_geojson: Mapped[str] = mapped_column(String(255), default="")
    ruta_mapa_calor_png: Mapped[str] = mapped_column(String(255), default="")
    creado_en: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )


def inicializar_bd_y_sembrar_lotes_tolima() -> None:
    """Crea las tablas en español e inserta las fincas y lotes arroceros de referencia en el Tolima."""
    BaseORM.metadata.create_all(bind=motor_bd)
    with SesionLocal() as sesion:
        if sesion.query(FincaORM).count() > 0:
            return

        fincas = [
            FincaORM(
                id="FINCA-TOL-01",
                nombre="Hacienda Arrocera San Isidro",
                municipio="El Espinal",
                distrito_riego="Usocoello",
                propietario="Agroindustrial del Tolima S.A.S.",
                area_total_ha=120.0,
            ),
            FincaORM(
                id="FINCA-TOL-02",
                nombre="Agrícola Las Palmas del Saldaña",
                municipio="Saldaña",
                distrito_riego="Usosaldaña",
                propietario="Inversiones Arroceras del Sur",
                area_total_ha=95.0,
            ),
        ]
        sesion.add_all(fincas)

        caja_espinal = ZONAS_ARROCERAS_TOLIMA["EL_ESPINAL"]["bbox"]
        caja_saldana = ZONAS_ARROCERAS_TOLIMA["SALDANA"]["bbox"]

        def _caja_a_wkt_y_geojson(
            caja: tuple[float, float, float, float]
        ) -> tuple[str, str]:
            min_lon, min_lat, max_lon, max_lat = caja
            # WKT y GeoJSON siguen los estándares internacionales OGC y RFC 7946
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

        wkt_1, geo_1 = _caja_a_wkt_y_geojson(caja_espinal)
        wkt_2, geo_2 = _caja_a_wkt_y_geojson(caja_saldana)

        lotes = [
            LoteORM(
                id="LOTE-ESPINAL-01",
                finca_id="FINCA-TOL-01",
                nombre="Lote Las Acacias - Sector Norte",
                municipio="El Espinal",
                variedad_arroz="Fedearroz 67",
                edad_cultivo_dias=58,
                area_ha=42.5,
                latitud_centro=ZONAS_ARROCERAS_TOLIMA["EL_ESPINAL"]["center_lat"],
                longitud_centro=ZONAS_ARROCERAS_TOLIMA["EL_ESPINAL"]["center_lon"],
                poligono_wkt=wkt_1,
                poligono_geojson=geo_1,
            ),
            LoteORM(
                id="LOTE-SALDANA-01",
                finca_id="FINCA-TOL-02",
                nombre="Lote El Canal - Distrito Saldaña",
                municipio="Saldaña",
                variedad_arroz="Fedearroz 2000",
                edad_cultivo_dias=45,
                area_ha=38.0,
                latitud_centro=ZONAS_ARROCERAS_TOLIMA["SALDANA"]["center_lat"],
                longitud_centro=ZONAS_ARROCERAS_TOLIMA["SALDANA"]["center_lon"],
                poligono_wkt=wkt_2,
                poligono_geojson=geo_2,
            ),
        ]
        sesion.add_all(lotes)

        detecciones_semilla = [
            DeteccionFitosanitariaORM(
                id_registro_cliente="SEMILLA-001",
                lote_id="LOTE-ESPINAL-01",
                tipo_fuente="DRON_VANT",
                etiqueta_enfermedad="sano",
                confianza=0.96,
                indice_severidad=0.02,
                latitud=4.1450,
                longitud=-74.8900,
                punto_wkt="POINT(-74.8900 4.1450)",
            ),
            DeteccionFitosanitariaORM(
                id_registro_cliente="SEMILLA-002",
                lote_id="LOTE-ESPINAL-01",
                tipo_fuente="DRON_VANT",
                etiqueta_enfermedad="roya_parda",
                confianza=0.92,
                indice_severidad=0.72,
                latitud=4.1486,
                longitud=-74.8830,
                punto_wkt="POINT(-74.8830 4.1486)",
            ),
            DeteccionFitosanitariaORM(
                id_registro_cliente="SEMILLA-003",
                lote_id="LOTE-ESPINAL-01",
                tipo_fuente="MOVIL_OFFLINE",
                etiqueta_enfermedad="roya_amarilla",
                confianza=0.89,
                indice_severidad=0.73,
                latitud=4.1515,
                longitud=-74.8780,
                punto_wkt="POINT(-74.8780 4.1515)",
            ),
        ]
        sesion.add_all(detecciones_semilla)
        sesion.commit()


def obtener_sesion_bd():
    sesion: Session = SesionLocal()
    try:
        yield sesion
    finally:
        sesion.close()


# Alias de compatibilidad
engine = motor_bd
SessionLocal = SesionLocal
Base = BaseORM
FarmORM = FincaORM
LotORM = LoteORM
PhytosanitaryDetectionORM = DeteccionFitosanitariaORM
OrthomosaicJobORM = TrabajoOrtomosaicoORM
init_db_and_seed_tolima_lots = inicializar_bd_y_sembrar_lotes_tolima
get_db = obtener_sesion_bd
