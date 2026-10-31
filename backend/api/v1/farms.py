"""
Endpoints de Gestión de Fincas y Lotes Arroceros en el Tolima (/api/v1/farms).
"""

from __future__ import annotations

import json

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.core.database import FarmORM, LotORM, get_db
from backend.schemas.api_schemas import LotSummarySchema

router = APIRouter(prefix="/farms", tags=["Fincas y Lotes Arroceros (Tolima)"])


@router.get("")
def list_farms(db: Session = Depends(get_db)):
    farms = db.query(FarmORM).all()
    return [
        {
            "id": f.id,
            "name": f.name,
            "municipality": f.municipality,
            "irrigation_district": f.irrigation_district,
            "owner_name": f.owner_name,
            "total_area_ha": f.total_area_ha,
        }
        for f in farms
    ]


@router.get("/lots", response_model=list[LotSummarySchema])
def list_lots(db: Session = Depends(get_db)):
    lots = db.query(LotORM).all()
    return [
        LotSummarySchema(
            id=lot.id,
            farm_id=lot.farm_id,
            name=lot.name,
            municipality=lot.municipality,
            rice_variety=lot.rice_variety,
            crop_age_days=lot.crop_age_days,
            area_ha=lot.area_ha,
            center_lat=lot.center_lat,
            center_lon=lot.center_lon,
            polygon_geojson=json.loads(lot.polygon_geojson),
        )
        for lot in lots
    ]


@router.get("/lots/{lot_id}", response_model=LotSummarySchema)
def get_lot_detail(lot_id: str, db: Session = Depends(get_db)):
    lot = db.query(LotORM).filter(LotORM.id == lot_id).first()
    if lot is None:
        raise HTTPException(status_code=404, detail=f"No existe el lote '{lot_id}'")
    return LotSummarySchema(
        id=lot.id,
        farm_id=lot.farm_id,
        name=lot.name,
        municipality=lot.municipality,
        rice_variety=lot.rice_variety,
        crop_age_days=lot.crop_age_days,
        area_ha=lot.area_ha,
        center_lat=lot.center_lat,
        center_lon=lot.center_lon,
        polygon_geojson=json.loads(lot.polygon_geojson),
    )
