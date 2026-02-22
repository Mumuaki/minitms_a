"""
GPS Integration Endpoints — интеграция с GPS Dozor.

Эндпоинты:
- GET /gps/vehicles — список транспортных средств с GPS координатами
- GET /gps/status — статус подключения к GPS сервису
"""

import os
import logging
from typing import List, Optional
from datetime import datetime

import httpx
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from backend.src.infrastructure.api.v1.dependencies import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/gps", tags=["GPS Integration"])

GPS_DOZOR_URL = os.getenv("GPS_DOZOR_URL", "https://a1.gpsguard.eu/api/v1/vehicle/")
GPS_DOZOR_USERNAME = os.getenv("GPS_DOZOR_USERNAME", "")
GPS_DOZOR_PASSWORD = os.getenv("GPS_DOZOR_PASSWORD", "")


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
    if not GPS_DOZOR_USERNAME or not GPS_DOZOR_PASSWORD:
        return []
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(
                GPS_DOZOR_URL,
                auth=(GPS_DOZOR_USERNAME, GPS_DOZOR_PASSWORD),
            )
            if response.status_code == 200:
                return response.json() if isinstance(response.json(), list) else []
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
    connected = False
    vehicles_count = 0
    message = "GPS Dozor credentials not configured"

    if GPS_DOZOR_USERNAME and GPS_DOZOR_PASSWORD:
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(
                    GPS_DOZOR_URL,
                    auth=(GPS_DOZOR_USERNAME, GPS_DOZOR_PASSWORD),
                )
                connected = response.status_code in (200, 201)
                if connected:
                    data = response.json()
                    vehicles_count = len(data) if isinstance(data, list) else 0
                    message = "Connected to GPS Dozor"
                else:
                    message = f"GPS Dozor returned HTTP {response.status_code}"
        except Exception as e:
            message = f"Connection failed: {str(e)}"
    else:
        message = "GPS_DOZOR_USERNAME or GPS_DOZOR_PASSWORD not set"

    return GPSStatus(
        connected=connected,
        provider="GPS Dozor",
        url=GPS_DOZOR_URL,
        vehicles_count=vehicles_count,
        last_sync=datetime.utcnow().isoformat() if connected else None,
        message=message,
    )
