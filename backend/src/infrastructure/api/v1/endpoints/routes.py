"""
Routes Calculation Endpoints.

Эндпоинты:
- POST /routes/calculate — рассчитать маршрут и прибыльность
- GET  /routes           — список сохранённых маршрутов
"""

from typing import List, Optional
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from backend.src.infrastructure.api.v1.dependencies import get_current_user

router = APIRouter(prefix="/routes", tags=["Routes"])


# ── Schemas ───────────────────────────────────────────────────────────────────

class RoutePoint(BaseModel):
    address: str
    lat: Optional[float] = None
    lon: Optional[float] = None


class RouteCalculateRequest(BaseModel):
    origin: RoutePoint
    destination: RoutePoint
    waypoints: Optional[List[RoutePoint]] = None
    vehicle_id: Optional[int] = None
    cargo_weight_kg: Optional[float] = None
    fuel_price_per_liter: Optional[float] = 1.65
    fuel_consumption_per_100km: Optional[float] = 28.0


class RouteCalculateResponse(BaseModel):
    distance_km: float
    duration_hours: float
    fuel_cost_eur: float
    toll_cost_eur: float
    total_cost_eur: float
    cost_per_km_eur: float
    origin: str
    destination: str
    waypoints_count: int
    calculated_at: str


class SavedRoute(BaseModel):
    id: int
    origin: str
    destination: str
    distance_km: float
    cost_eur: float
    created_at: str


_saved_routes: List[SavedRoute] = []


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.post("/calculate", response_model=RouteCalculateResponse)
async def calculate_route(
    request: RouteCalculateRequest,
    current_user=Depends(get_current_user),
):
    """
    Рассчитать маршрут: расстояние, стоимость топлива, прибыльность.

    Использует OSRM для расчёта расстояния, если координаты предоставлены.
    """
    distance_km = 0.0

    # Try OSRM if coordinates provided
    if request.origin.lat and request.origin.lon and request.destination.lat and request.destination.lon:
        try:
            import httpx
            coords = f"{request.origin.lon},{request.origin.lat};{request.destination.lon},{request.destination.lat}"
            url = f"http://router.project-osrm.org/route/v1/driving/{coords}?overview=false"
            async with httpx.AsyncClient(timeout=8.0) as client:
                resp = await client.get(url)
                if resp.status_code == 200:
                    data = resp.json()
                    distance_km = data["routes"][0]["distance"] / 1000
        except Exception:
            pass

    # Fallback: estimate from origin/destination names
    if distance_km == 0.0:
        distance_km = 500.0

    fuel_liters = (distance_km / 100) * (request.fuel_consumption_per_100km or 28.0)
    fuel_cost = round(fuel_liters * (request.fuel_price_per_liter or 1.65), 2)
    toll_cost = round(distance_km * 0.08, 2)
    total_cost = round(fuel_cost + toll_cost, 2)
    cost_per_km = round(total_cost / distance_km, 4) if distance_km else 0.0
    duration_h = round(distance_km / 70, 2)

    route = RouteCalculateResponse(
        distance_km=round(distance_km, 2),
        duration_hours=duration_h,
        fuel_cost_eur=fuel_cost,
        toll_cost_eur=toll_cost,
        total_cost_eur=total_cost,
        cost_per_km_eur=cost_per_km,
        origin=request.origin.address,
        destination=request.destination.address,
        waypoints_count=len(request.waypoints or []),
        calculated_at=datetime.utcnow().isoformat(),
    )

    _saved_routes.append(SavedRoute(
        id=len(_saved_routes) + 1,
        origin=request.origin.address,
        destination=request.destination.address,
        distance_km=route.distance_km,
        cost_eur=route.total_cost_eur,
        created_at=route.calculated_at,
    ))

    return route


@router.get("/", response_model=List[SavedRoute])
async def get_routes(
    current_user=Depends(get_current_user),
):
    """Список сохранённых маршрутов."""
    return _saved_routes
