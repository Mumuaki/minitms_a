from pydantic import BaseModel
from typing import Optional
from enum import Enum

class VehicleStatus(str, Enum):
    FREE = "Free"
    IN_TRANSIT = "In Transit"
    MAINTENANCE = "Maintenance"
    UNAVAILABLE = "Unavailable"

class VehicleType(str, Enum):
    TENT = "Tent"
    REEFER = "Reefer"
    CONTAINER = "Container"
    OTHER = "Other"

class VehicleBase(BaseModel):
    license_plate: str
    vehicle_type: VehicleType
    length: float
    width: float
    height: float
    payload_capacity: int
    gps_tracker_id: Optional[str] = None

class VehicleCreate(VehicleBase):
    pass

from datetime import datetime

class VehicleResponse(VehicleBase):
    id: int
    status: VehicleStatus
    current_location: Optional[str] = None
    gps_last_updated: Optional[datetime] = None
    
    class Config:
        from_attributes = True
