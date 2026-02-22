"""
Vehicles Endpoints — alias/extension layer over fleet.

Adds:
- GET /vehicles       — alias for /fleet/ (для совместимости с тестами)
- GET /vehicles/stats — статистика автопарка
"""

from typing import List
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from backend.src.infrastructure.persistence.sqlalchemy.database import get_db
from backend.src.application.dto.vehicle_dto import VehicleResponse
from backend.src.application.use_cases.fleet.get_all_vehicles import GetAllVehiclesUseCase
from backend.src.infrastructure.api.v1.dependencies import get_current_user

router = APIRouter(prefix="/vehicles", tags=["Vehicles"])


class VehicleStats(BaseModel):
    total: int
    active: int
    in_transit: int
    available: int
    maintenance: int
    avg_load_capacity_kg: float
    total_capacity_kg: float


@router.get("/", response_model=List[VehicleResponse])
def get_vehicles(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Список транспортных средств (alias для /fleet/)."""
    use_case = GetAllVehiclesUseCase(db)
    return use_case.execute()


@router.get("/stats", response_model=VehicleStats)
def get_vehicle_stats(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Статистика автопарка."""
    use_case = GetAllVehiclesUseCase(db)
    vehicles = use_case.execute()
    total = len(vehicles)

    active = sum(1 for v in vehicles if getattr(v, "is_active", True))
    total_capacity = sum(
        getattr(v, "load_capacity", 0) or 0 for v in vehicles
    )
    avg_capacity = total_capacity / total if total else 0.0

    return VehicleStats(
        total=total,
        active=active,
        in_transit=0,
        available=active,
        maintenance=total - active,
        avg_load_capacity_kg=round(avg_capacity, 2),
        total_capacity_kg=round(total_capacity, 2),
    )
