"""
GPS Integration Endpoints — интеграция с GPS Dozor.

Эндпоинты:
- GET /gps/vehicles — список транспортных средств с GPS координатами
- GET /gps/status — статус подключения к GPS сервису
"""

import logging
from typing import List, Optional
from datetime import datetime

import httpx
from fastapi import APIRouter, Depends
from pydantic import BaseModel

from backend.src.infrastructure.api.v1.dependencies import get_current_user
from backend.src.infrastructure.config.settings import settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/gps", tags=["GPS Integration"])


class GPSVehicle(BaseModel):
    id: str
    name: str
    license_plate: Optional[str] = None
    lat: Optional[float] = None
    lon: Optional[float] = None
    speed: Optional[float] = None
    last_update: Optional[str] = None
    status: str = "unknown"


class GPSStatus(BaseModel):
    connected: bool
    provider: str
    url: str
    vehicles_count: int
    last_sync: Optional[str] = None
    message: str


async def _fetch_gps_vehicles() -> list:
    """Fetch vehicle data from GPS Dozor API."""
    username = settings.GPS_DOZOR_USERNAME.strip()
    password = settings.GPS_DOZOR_PASSWORD.strip()
    url = settings.GPS_DOZOR_URL
    if not username or not password:
        return []
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(url, auth=(username, password))
            if response.status_code == 200:
                data = response.json()
                if isinstance(data, list):
                    return data
                # Handle wrapped responses: {"data": [...], "vehicles": [...], etc.}
                if isinstance(data, dict):
                    for key in ("data", "vehicles", "items", "results", "list"):
                        val = data.get(key)
                        if isinstance(val, list):
                            return val
    except Exception as e:
        logger.warning("GPS Dozor fetch failed: %s", e)
    return []


@router.get("/vehicles", response_model=List[GPSVehicle])
async def get_gps_vehicles(
    current_user=Depends(get_current_user),
):
    """Список транспортных средств с GPS координатами."""
    raw = await _fetch_gps_vehicles()
    vehicles = []
    for item in raw:
        vehicles.append(GPSVehicle(
            id=str(item.get("id", item.get("vehicle_id", ""))),
            name=item.get("name", item.get("title", "Unknown")),
            license_plate=item.get("license_plate", item.get("plate")),
            lat=item.get("lat", item.get("latitude")),
            lon=item.get("lon", item.get("longitude")),
            speed=item.get("speed"),
            last_update=item.get("last_update", item.get("updated_at")),
            status=item.get("status", "active"),
        ))
    return vehicles


@router.get("/status", response_model=GPSStatus)
async def get_gps_status(
    current_user=Depends(get_current_user),
):
    """Статус подключения к GPS провайдеру."""
    username = settings.GPS_DOZOR_USERNAME.strip()
    password = settings.GPS_DOZOR_PASSWORD.strip()
    url = settings.GPS_DOZOR_URL
    connected = False
    vehicles_count = 0
    message = "GPS Dozor credentials not configured"

    if username and password:
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(url, auth=(username, password))
                connected = response.status_code in (200, 201)
                if connected:
                    data = response.json()
                    if isinstance(data, list):
                        vehicles_count = len(data)
                    elif isinstance(data, dict):
                        for key in ("data", "vehicles", "items", "results", "list"):
                            val = data.get(key)
                            if isinstance(val, list):
                                vehicles_count = len(val)
                                break
                    message = f"Connected to GPS Dozor ({vehicles_count} vehicles)"
                else:
                    message = f"GPS Dozor returned HTTP {response.status_code}"
        except Exception as e:
            message = f"Connection failed: {str(e)}"
    else:
        message = "GPS_DOZOR_USERNAME or GPS_DOZOR_PASSWORD not set in backend/.env"

    return GPSStatus(
        connected=connected,
        provider="GPS Dozor",
        url=url,
        vehicles_count=vehicles_count,
        last_sync=datetime.utcnow().isoformat() if connected else None,
        message=message,
    )
