"""
DTOs for Cargo operations.
"""

from datetime import date
from typing import List, Optional
from pydantic import BaseModel, Field
from enum import Enum


class CargoStatusColor(str, Enum):
    RED = "RED"
    GRAY = "GRAY"
    YELLOW = "YELLOW"
    GREEN = "GREEN"


class LocationDto(BaseModel):
    address: str
    country_code: str
    lat: float
    lon: float


class ProfitabilityDto(BaseModel):
    rate_per_km: Optional[float]
    empty_run_km: Optional[float]
    total_distance: Optional[float]
    color_code: CargoStatusColor


class CargoDto(BaseModel):
    id: str
    external_id: str
    source: str
    loading_place: LocationDto
    unloading_place: LocationDto
    loading_date: Optional[date]
    unloading_date: Optional[date]
    weight: Optional[float]
    body_type: Optional[str]
    price: Optional[float]
    distance_trans_eu: Optional[int]
    distance_osm: Optional[int]
    profitability: Optional[ProfitabilityDto]
    is_hidden: bool
    created_at: str  # ISO format


class SearchCargoRequestDto(BaseModel):
    # Filters
    loading_date_from: Optional[date] = None
    loading_date_to: Optional[date] = None
    unloading_date_from: Optional[date] = None
    unloading_date_to: Optional[date] = None
    weight_min: Optional[float] = None
    weight_max: Optional[float] = None
    body_type: Optional[str] = None
    price_min: Optional[float] = None
    price_max: Optional[float] = None
    distance_min: Optional[int] = None
    distance_max: Optional[int] = None
    distance_type: Optional[str] = Field("trans_eu", description="trans_eu or osm")
    status_colors: Optional[List[CargoStatusColor]] = None
    source: Optional[str] = None
    is_hidden: Optional[bool] = None

    # Vehicle-based filters
    vehicle_body_type: Optional[str] = Field(None, description="Тип кузова транспортного средства")
    vehicle_max_weight: Optional[float] = Field(None, description="Максимальный вес груза для ТС (т)")
    vehicle_capacity: Optional[float] = Field(None, description="Вместимость ТС (м³)")
    vehicle_length: Optional[float] = Field(None, description="Длина ТС (м)")
    vehicle_width: Optional[float] = Field(None, description="Ширина ТС (м)")
    vehicle_height: Optional[float] = Field(None, description="Высота ТС (м)")

    # Profitability calculation parameters
    fuel_consumption: Optional[float] = Field(None, description="Fuel consumption (l/100km)", ge=0)
    fuel_price: Optional[float] = Field(None, description="Fuel price (€/l)", ge=0)
    depreciation_per_km: Optional[float] = Field(None, description="Depreciation (€/km)", ge=0)
    driver_salary_per_km: Optional[float] = Field(None, description="Driver salary (€/km)", ge=0)
    other_costs_per_km: Optional[float] = Field(None, description="Other costs (€/km)", ge=0)
    empty_run_distance: Optional[float] = Field(0, description="Empty run distance (km)", ge=0)

    # Sorting
    order_by: Optional[str] = Field("created_at", description="Field to order by")
    order_direction: Optional[str] = Field("desc", description="asc or desc")

    # Pagination
    page: int = Field(1, ge=1)
    limit: int = Field(20, ge=1, le=100)


class SearchCargoResponseDto(BaseModel):
    items: List[CargoDto]
    total: int
    page: int
    limit: int
    total_pages: int