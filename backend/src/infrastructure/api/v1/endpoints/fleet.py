from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional

from backend.src.infrastructure.persistence.sqlalchemy.database import get_db
from backend.src.application.dto.vehicle_dto import VehicleCreate, VehicleResponse
from backend.src.application.use_cases.fleet.add_vehicle import AddVehicleUseCase
from backend.src.application.use_cases.fleet.get_all_vehicles import GetAllVehiclesUseCase
from backend.src.application.use_cases.fleet.update_vehicle import UpdateVehicleUseCase
from backend.src.application.use_cases.fleet.delete_vehicle import DeleteVehicleUseCase
from backend.src.application.use_cases.fleet.refresh_vehicle_location import RefreshVehicleLocationUseCase
from backend.src.infrastructure.api.v1.dependencies import get_current_user, require_role
from pydantic import BaseModel
from backend.src.domain.entities.vehicle import Vehicle, VehicleStatus as EntityVehicleStatus
from datetime import date, datetime
from backend.src.domain.entities.order import Order
from backend.src.domain.entities.vehicle_position import VehiclePosition

router = APIRouter(prefix="/fleet", tags=["Fleet"])

@router.post("/", response_model=VehicleResponse)
def create_vehicle(
    vehicle: VehicleCreate, 
    db: Session = Depends(get_db),
    current_user = Depends(require_role(['administrator','director','dispatcher']))
):
    use_case = AddVehicleUseCase(db)
    return use_case.execute(vehicle)

@router.get("/", response_model=List[VehicleResponse])
def get_vehicles(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    use_case = GetAllVehiclesUseCase(db)
    return use_case.execute()

@router.put("/{vehicle_id}", response_model=VehicleResponse)
def update_vehicle(
    vehicle_id: int,
    vehicle: VehicleCreate,
    db: Session = Depends(get_db),
    current_user = Depends(require_role(['administrator','director','dispatcher']))
):
    use_case = UpdateVehicleUseCase(db)
    updated_vehicle = use_case.execute(vehicle_id, vehicle)
    if not updated_vehicle:
        raise HTTPException(status_code=404, detail="Vehicle not found")
    return updated_vehicle

@router.delete("/{vehicle_id}")
def delete_vehicle(
    vehicle_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(require_role(['administrator','director'])),
):
    use_case = DeleteVehicleUseCase(db)
    success = use_case.execute(vehicle_id)
    if not success:
        raise HTTPException(status_code=404, detail="Vehicle not found")
    return {"status": "success", "message": "Vehicle deleted"}


@router.post("/{vehicle_id}/refresh-location", response_model=VehicleResponse)
def refresh_vehicle_location(
    vehicle_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(require_role(['administrator','director','dispatcher'])),
):
    """Refresh vehicle's current_location from GPS (Dozor/Guard). Fleet card will show actual location."""
    use_case = RefreshVehicleLocationUseCase(db)
    updated = use_case.execute(vehicle_id)
    if not updated:
        raise HTTPException(status_code=404, detail="Vehicle not found")
    return updated



class VehiclePositionItem(BaseModel):
    id: int
    latitude: Optional[float]
    longitude: Optional[float]
    place_name: Optional[str]
    country_code: Optional[str]
    measured_at: Optional[datetime]
    created_at: Optional[datetime]


@router.get("/{vehicle_id}/positions", response_model=List[VehiclePositionItem])
def get_vehicle_positions(
    vehicle_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),
):
    """История перемещений ТС (FR-GPS-004)."""
    positions = (
        db.query(VehiclePosition)
        .filter(VehiclePosition.vehicle_id == vehicle_id)
        .order_by(VehiclePosition.measured_at.desc())
        .limit(200)
        .all()
    )
    return [
        VehiclePositionItem(
            id=p.id,
            latitude=p.latitude,
            longitude=p.longitude,
            place_name=p.place_name,
            country_code=p.country_code,
            measured_at=p.measured_at,
            created_at=p.created_at,
        )
        for p in positions
    ]


class StatusUpdate(BaseModel):
    status: str


@router.patch("/{vehicle_id}/status", response_model=VehicleResponse)
def update_vehicle_status(
    vehicle_id: int,
    payload: StatusUpdate,
    db: Session = Depends(get_db),
    current_user = Depends(require_role(['administrator','director','dispatcher']))
):
    """Установить статус ТС: Free / In Transit / Maintenance / Unavailable."""
    valid = {s.value for s in EntityVehicleStatus}
    if payload.status not in valid:
        raise HTTPException(status_code=400, detail="Invalid status. Allowed: " + str(sorted(valid)))
    vehicle = db.query(Vehicle).filter(Vehicle.id == vehicle_id).first()
    if not vehicle:
        raise HTTPException(status_code=404, detail="Vehicle not found")
    vehicle.status = EntityVehicleStatus(payload.status)
    db.commit()
    db.refresh(vehicle)
    return VehicleResponse.model_validate(vehicle)



class TripHistoryItem(BaseModel):
    id: int
    start_date: date
    end_date: date
    revenue: float
    margin: float
    distance: float
    status: str


@router.get("/{vehicle_id}/history", response_model=List[TripHistoryItem])
def get_vehicle_history(
    vehicle_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),
):
    """История рейсов ТС (FR-FLEET-004) — из фактических заказов."""
    orders = db.query(Order).filter(Order.vehicle_id == vehicle_id).order_by(Order.start_date.desc()).all()
    return [
        TripHistoryItem(
            id=o.id,
            start_date=o.start_date,
            end_date=o.end_date,
            revenue=o.revenue,
            margin=o.margin,
            distance=o.distance,
            status=o.status.value if hasattr(o.status, "value") else o.status,
        )
        for o in orders
    ]



@router.get("/export")
def export_fleet(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),
):
    """Экспорт автопарка в CSV (FR-FLEET-006), включая размеры кузова L×W×H."""
    from fastapi.responses import Response
    vehicles = db.query(Vehicle).order_by(Vehicle.id.asc()).all()
    header = ["license_plate", "vehicle_type", "length_m", "width_m", "height_m", "payload_capacity_kg", "status", "gps_tracker_id", "current_location"]
    lines = [";".join(header)]
    for v in vehicles:
        lines.append(";".join([
            v.license_plate,
            v.vehicle_type.value if hasattr(v.vehicle_type, "value") else str(v.vehicle_type),
            str(v.length), str(v.width), str(v.height),
            str(v.payload_capacity),
            v.status.value if hasattr(v.status, "value") else str(v.status),
            v.gps_tracker_id or "",
            v.current_location or "",
        ]))
    return Response(content=chr(10).join(lines), media_type="text/csv", headers={"Content-Disposition": "attachment; filename=fleet.csv"})
