from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from backend.src.infrastructure.persistence.sqlalchemy.database import get_db
from backend.src.application.dto.vehicle_dto import VehicleCreate, VehicleResponse
from backend.src.application.use_cases.fleet.add_vehicle import AddVehicleUseCase
from backend.src.application.use_cases.fleet.get_all_vehicles import GetAllVehiclesUseCase
from backend.src.application.use_cases.fleet.update_vehicle import UpdateVehicleUseCase
from backend.src.application.use_cases.fleet.delete_vehicle import DeleteVehicleUseCase
from backend.src.application.use_cases.fleet.refresh_vehicle_location import RefreshVehicleLocationUseCase
from backend.src.infrastructure.api.v1.dependencies import get_current_user

router = APIRouter(prefix="/fleet", tags=["Fleet"])

@router.post("/", response_model=VehicleResponse)
def create_vehicle(
    vehicle: VehicleCreate, 
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
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
    current_user = Depends(get_current_user)
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
    current_user=Depends(get_current_user),
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
    current_user=Depends(get_current_user),
):
    """Refresh vehicle's current_location from GPS (Dozor/Guard). Fleet card will show actual location."""
    use_case = RefreshVehicleLocationUseCase(db)
    updated = use_case.execute(vehicle_id)
    if not updated:
        raise HTTPException(status_code=404, detail="Vehicle not found")
    return updated
