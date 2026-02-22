"""
GPS Integration Endpoints.

GET /gps/vehicles — list of vehicles with GPS data from GPS Guard
GET /gps/status  — connection status to GPS Guard provider
"""
import logging
from datetime import datetime, timezone
from typing import List, Optional

import httpx
from fastapi import APIRouter, Depends
from pydantic import BaseModel

from backend.src.infrastructure.api.v1.dependencies import get_current_user
from backend.src.infrastructure.config.settings import settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/gps", tags=["GPS Integration"])


def _base_url() -> str:
    url = settings.GPS_DOZOR_URL.rstrip("/")
    for suffix in ("/vehicle", "/vehicles"):
        if url.endswith(suffix):
            url = url[: -len(suffix)]
    return url  # https://a1.gpsguard.eu/api/v1


def _auth() -> tuple:
    return settings.GPS_DOZOR_USERNAME.strip(), settings.GPS_DOZOR_PASSWORD.strip()


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


async def _fetch_all_vehicles() -> list:
    """Fetch all vehicles via groups → vehicles/group/{code}."""
    username, password = _auth()
    if not username or not password:
        return []
    base = _base_url()
    auth = (username, password)
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            # Step 1: get groups
            r = await client.get(f"{base}/groups", auth=auth)
            if r.status_code != 200:
                logger.warning("GPS Guard /groups HTTP %s", r.status_code)
                return []
            groups = r.json() if isinstance(r.json(), list) else []

            # Step 2: get vehicles per group
            all_vehicles: list = []
            for group in groups:
                code = group.get("Code", "")
                vr = await client.get(f"{base}/vehicles/group/{code}", auth=auth)
                if vr.status_code == 200:
                    data = vr.json()
                    if isinstance(data, list):
                        all_vehicles.extend(data)
            return all_vehicles
    except Exception as e:
        logger.warning("GPS Guard fetch failed: %s", e)
        return []


@router.get("/vehicles", response_model=List[GPSVehicle])
async def get_gps_vehicles(current_user=Depends(get_current_user)):
    """List of vehicles with GPS coordinates from GPS Guard."""
    raw = await _fetch_all_vehicles()
    result = []
    for item in raw:
        pos = item.get("LastPosition") or {}
        lat_s = pos.get("Latitude")
        lon_s = pos.get("Longitude")
        try:
            lat = float(lat_s) if lat_s is not None else None
            lon = float(lon_s) if lon_s is not None else None
        except (ValueError, TypeError):
            lat = lon = None
        result.append(GPSVehicle(
            id=str(item.get("Code", "")),
            name=item.get("Name") or item.get("Code") or "Unknown",
            license_plate=item.get("SPZ") or item.get("Name"),
            lat=lat,
            lon=lon,
            speed=item.get("Speed"),
            last_update=item.get("LastPositionTimestamp"),
            status="active" if item.get("IsActive") else "inactive",
        ))
    return result


@router.get("/status", response_model=GPSStatus)
async def get_gps_status(current_user=Depends(get_current_user)):
    """Connection status to GPS Guard provider."""
    username, password = _auth()
    base = _base_url()
    connected = False
    vehicles_count = 0
    message = "GPS_DOZOR_USERNAME or GPS_DOZOR_PASSWORD not set in backend/.env"

    if username and password:
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                r = await client.get(f"{base}/groups", auth=(username, password))
                if r.status_code == 200:
                    groups = r.json() if isinstance(r.json(), list) else []
                    connected = True
                    # Count vehicles across all groups
                    for group in groups:
                        code = group.get("Code", "")
                        vr = await client.get(
                            f"{base}/vehicles/group/{code}",
                            auth=(username, password),
                        )
                        if vr.status_code == 200:
                            data = vr.json()
                            if isinstance(data, list):
                                vehicles_count += len(data)
                    message = (
                        f"Connected to GPS Guard ({len(groups)} group(s), "
                        f"{vehicles_count} vehicle(s))"
                    )
                else:
                    message = f"GPS Guard /groups returned HTTP {r.status_code}"
        except Exception as e:
            message = f"Connection failed: {e}"

    return GPSStatus(
        connected=connected,
        provider="GPS Guard (a1.gpsguard.eu)",
        url=base,
        vehicles_count=vehicles_count,
        last_sync=datetime.now(timezone.utc).isoformat() if connected else None,
        message=message,
    )
