"""
Cargo Endpoints — REST API для работы с грузами.

Эндпоинты:
- GET /cargos/search — поиск грузов с фильтрами
"""

from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from typing import Optional, List
from datetime import date

from backend.src.infrastructure.persistence.sqlalchemy.database import get_db
from backend.src.domain.repositories.cargo_repository import CargoRepository
from backend.src.infrastructure.persistence.sqlalchemy.repositories.cargo_repository_impl import CargoRepositoryImpl
from backend.src.application.use_cases.cargo.search_cargos import SearchCargosUseCase
from backend.src.application.use_cases.cargo.filter_by_vehicle import FilterByVehicleUseCase
from backend.src.application.dto.cargo_dto import SearchCargoRequestDto, CargoStatusColor
from backend.src.infrastructure.api.v1.schemas.cargo_schema import (
    SearchCargoRequest,
    SearchCargoResponse,
    ErrorResponse
)


# Роутер с префиксом /cargos
router = APIRouter(prefix="/cargos", tags=["Cargos"])


from backend.src.application.use_cases.cargo.import_trans_eu_offers import ImportTransEuOffersUseCase

# ============================================================================
# DEPENDENCIES
# ============================================================================

def get_cargo_repository(db: Session = Depends(get_db)) -> CargoRepository:
    """Dependency для получения репозитория грузов."""
    return CargoRepositoryImpl(db)


def get_search_cargos_use_case(repo: CargoRepository = Depends(get_cargo_repository)) -> SearchCargosUseCase:
    """Dependency для получения use case поиска грузов."""
    return SearchCargosUseCase(repo)


def get_filter_by_vehicle_use_case(repo: CargoRepository = Depends(get_cargo_repository)) -> FilterByVehicleUseCase:
    """Dependency для получения use case фильтрации по ТС."""
    return FilterByVehicleUseCase(repo)

def get_import_trans_eu_offers_use_case(repo: CargoRepository = Depends(get_cargo_repository)) -> ImportTransEuOffersUseCase:
    """Dependency для получения use case импорта грузов."""
    return ImportTransEuOffersUseCase(repo)


# ============================================================================
# ENDPOINTS
# ============================================================================

@router.post(
    "/import_trans_eu",
    response_model=List[dict], # Simplification for now, returning raw DTOs or items
    summary="Запуск импорта из Trans.eu",
    description="Запускает скрапинг Trans.eu по заданным параметрам и сохраняет результаты в БД."
)
async def import_trans_eu(
    loading: str = Query(..., description="Место загрузки"),
    unloading: str = Query(..., description="Место выгрузки"),
    loading_radius: int = Query(75, description="Радиус загрузки"),
    unloading_radius: int = Query(75, description="Радиус выгрузки"),
    date_from: Optional[str] = Query(None, description="Дата загрузки с (DD.MM.YYYY)"),
    date_to: Optional[str] = Query(None, description="Дата загрузки по (DD.MM.YYYY)"),
    unloading_date_from: Optional[str] = Query(None, description="Дата выгрузки с (DD.MM.YYYY)"),
    unloading_date_to: Optional[str] = Query(None, description="Дата выгрузки по (DD.MM.YYYY)"),
    weight_to: str = Query("0.9", description="Макс вес"),
    length_to: Optional[str] = Query(None, description="Макс длина"),
    use_case: ImportTransEuOffersUseCase = Depends(get_import_trans_eu_offers_use_case)
):
    try:
        result = await use_case.execute(
            loading=loading,
            unloading=unloading,
            loading_radius=loading_radius,
            unloading_radius=unloading_radius,
            date_from=date_from,
            date_to=date_to,
            unloading_date_from=unloading_date_from,
            unloading_date_to=unloading_date_to,
            weight_to=weight_to,
            length_to=length_to
        )
        # return result # return raw DTOs
        # Simple serialization for response
        return [c.dict() for c in result]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/search",
    response_model=SearchCargoResponse,
    responses={400: {"model": ErrorResponse}, 422: {"model": ErrorResponse}},
    summary="Поиск грузов",
    description="Поиск грузов с расширенными фильтрами, сортировкой и пагинацией.",
)
async def search_cargos(
    # Filters
    loading_date_from: Optional[str] = Query(None, description="Начальная дата загрузки (YYYY-MM-DD)"),
    loading_date_to: Optional[str] = Query(None, description="Конечная дата загрузки (YYYY-MM-DD)"),
    unloading_date_from: Optional[str] = Query(None, description="Начальная дата выгрузки (YYYY-MM-DD)"),
    unloading_date_to: Optional[str] = Query(None, description="Конечная дата выгрузки (YYYY-MM-DD)"),
    weight_min: Optional[float] = Query(None, description="Минимальный вес (т)", ge=0),
    weight_max: Optional[float] = Query(None, description="Максимальный вес (т)", ge=0),
    body_type: Optional[str] = Query(None, description="Тип кузова"),
    price_min: Optional[float] = Query(None, description="Минимальная цена (€)", ge=0),
    price_max: Optional[float] = Query(None, description="Максимальная цена (€)", ge=0),
    distance_min: Optional[int] = Query(None, description="Минимальное расстояние (км)", ge=0),
    distance_max: Optional[int] = Query(None, description="Максимальное расстояние (км)", ge=0),
    distance_type: Optional[str] = Query("trans_eu", description="Тип расстояния: trans_eu или osm"),
    status_colors: Optional[List[str]] = Query(None, description="Статусы цвета рентабельности"),
    source: Optional[str] = Query(None, description="Источник данных"),
    is_hidden: Optional[bool] = Query(None, description="Показывать скрытые грузы"),

    # Profitability calculation parameters
    fuel_consumption: Optional[float] = Query(None, description="Расход топлива (л/100км)", ge=0),
    fuel_price: Optional[float] = Query(None, description="Стоимость топлива (€/л)", ge=0),
    depreciation_per_km: Optional[float] = Query(None, description="Амортизация (€/км)", ge=0),
    driver_salary_per_km: Optional[float] = Query(None, description="Зарплата водителя (€/км)", ge=0),
    other_costs_per_km: Optional[float] = Query(None, description="Прочие расходы (€/км)", ge=0),
    empty_run_distance: Optional[float] = Query(0, description="Расстояние порожнего пробега (км)", ge=0),

    # Sorting
    order_by: Optional[str] = Query("created_at", description="Поле сортировки"),
    order_direction: Optional[str] = Query("desc", description="Направление сортировки: asc или desc"),

    # Pagination
    page: int = Query(1, description="Номер страницы", ge=1),
    limit: int = Query(20, description="Количество элементов на странице", ge=1, le=100),

    # Vehicle-based filters
    vehicle_body_type: Optional[str] = Query(None, description="Тип кузова транспортного средства"),
    vehicle_max_weight: Optional[float] = Query(None, description="Максимальный вес груза для ТС (т)", ge=0),
    vehicle_capacity: Optional[float] = Query(None, description="Вместимость ТС (м³)", ge=0),
    vehicle_length: Optional[float] = Query(None, description="Длина ТС (м)", ge=0),
    vehicle_width: Optional[float] = Query(None, description="Ширина ТС (м)", ge=0),
    vehicle_height: Optional[float] = Query(None, description="Высота ТС (м)", ge=0),

    use_case: SearchCargosUseCase = Depends(get_search_cargos_use_case)
) -> SearchCargoResponse:
    """
    Поиск грузов с фильтрами.

    Поддерживает фильтры по датам, весу, цене, расстоянию, типу кузова и т.д.
    """
    try:
        # Преобразуем параметры запроса в DTO
        request_dto = SearchCargoRequestDto(
            loading_date_from=_parse_date(loading_date_from),
            loading_date_to=_parse_date(loading_date_to),
            unloading_date_from=_parse_date(unloading_date_from),
            unloading_date_to=_parse_date(unloading_date_to),
            weight_min=weight_min,
            weight_max=weight_max,
            body_type=body_type,
            price_min=price_min,
            price_max=price_max,
            distance_min=distance_min,
            distance_max=distance_max,
            distance_type=distance_type,
            status_colors=[CargoStatusColor(color) for color in status_colors] if status_colors else None,
            source=source,
            is_hidden=is_hidden,
            fuel_consumption=fuel_consumption,
            fuel_price=fuel_price,
            depreciation_per_km=depreciation_per_km,
            driver_salary_per_km=driver_salary_per_km,
            other_costs_per_km=other_costs_per_km,
            empty_run_distance=empty_run_distance,
            order_by=order_by,
            order_direction=order_direction,
            page=page,
            limit=limit,
            vehicle_body_type=vehicle_body_type,
            vehicle_max_weight=vehicle_max_weight,
            vehicle_capacity=vehicle_capacity,
            vehicle_length=vehicle_length,
            vehicle_width=vehicle_width,
            vehicle_height=vehicle_height
        )

        # Выполняем поиск
        result = use_case.execute(request_dto)

        # Преобразуем результат в схему ответа
        return SearchCargoResponse(
            items=result.items,
            total=result.total,
            page=result.page,
            limit=result.limit,
            total_pages=result.total_pages
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get(
    "/filter-by-vehicle",
    response_model=SearchCargoResponse,
    responses={400: {"model": ErrorResponse}, 422: {"model": ErrorResponse}},
    summary="Фильтрация грузов по транспортному средству",
    description="Фильтрация грузов на основе характеристик транспортного средства: тип кузова, вес, габариты и т.д.",
)
async def filter_cargos_by_vehicle(
    # Vehicle characteristics
    vehicle_body_type: Optional[str] = Query(None, description="Тип кузова транспортного средства"),
    vehicle_max_weight: Optional[float] = Query(None, description="Максимальный вес груза для ТС (т)", ge=0),
    vehicle_capacity: Optional[float] = Query(None, description="Вместимость ТС (м³)", ge=0),
    vehicle_length: Optional[float] = Query(None, description="Длина ТС (м)", ge=0),
    vehicle_width: Optional[float] = Query(None, description="Ширина ТС (м)", ge=0),
    vehicle_height: Optional[float] = Query(None, description="Высота ТС (м)", ge=0),

    # Profitability calculation parameters
    fuel_consumption: Optional[float] = Query(None, description="Расход топлива (л/100км)", ge=0),
    fuel_price: Optional[float] = Query(None, description="Стоимость топлива (€/л)", ge=0),
    depreciation_per_km: Optional[float] = Query(None, description="Амортизация (€/км)", ge=0),
    driver_salary_per_km: Optional[float] = Query(None, description="Зарплата водителя (€/км)", ge=0),
    other_costs_per_km: Optional[float] = Query(None, description="Прочие расходы (€/км)", ge=0),
    empty_run_distance: Optional[float] = Query(0, description="Расстояние порожнего пробега (км)", ge=0),

    # Additional filters (same as search)
    loading_date_from: Optional[str] = Query(None, description="Начальная дата загрузки (YYYY-MM-DD)"),
    loading_date_to: Optional[str] = Query(None, description="Конечная дата загрузки (YYYY-MM-DD)"),
    unloading_date_from: Optional[str] = Query(None, description="Начальная дата выгрузки (YYYY-MM-DD)"),
    unloading_date_to: Optional[str] = Query(None, description="Конечная дата выгрузки (YYYY-MM-DD)"),
    weight_min: Optional[float] = Query(None, description="Минимальный вес (т)", ge=0),
    weight_max: Optional[float] = Query(None, description="Максимальный вес (т)", ge=0),
    price_min: Optional[float] = Query(None, description="Минимальная цена (€)", ge=0),
    price_max: Optional[float] = Query(None, description="Максимальная цена (€)", ge=0),
    distance_min: Optional[int] = Query(None, description="Минимальное расстояние (км)", ge=0),
    distance_max: Optional[int] = Query(None, description="Максимальное расстояние (км)", ge=0),
    distance_type: Optional[str] = Query("trans_eu", description="Тип расстояния: trans_eu или osm"),
    status_colors: Optional[List[str]] = Query(None, description="Статусы цвета рентабельности"),
    source: Optional[str] = Query(None, description="Источник данных"),
    is_hidden: Optional[bool] = Query(None, description="Показывать скрытые грузы"),

    # Sorting
    order_by: Optional[str] = Query("created_at", description="Поле сортировки"),
    order_direction: Optional[str] = Query("desc", description="Направление сортировки: asc или desc"),

    # Pagination
    page: int = Query(1, description="Номер страницы", ge=1),
    limit: int = Query(20, description="Количество элементов на странице", ge=1, le=100),

    use_case: FilterByVehicleUseCase = Depends(get_filter_by_vehicle_use_case)
) -> SearchCargoResponse:
    """
    Фильтрация грузов по характеристикам транспортного средства.
    """
    try:
        # Преобразуем параметры запроса
        search_params = {
            "loading_date_from": _parse_date(loading_date_from),
            "loading_date_to": _parse_date(loading_date_to),
            "unloading_date_from": _parse_date(unloading_date_from),
            "unloading_date_to": _parse_date(unloading_date_to),
            "weight_min": weight_min,
            "weight_max": weight_max,
            "price_min": price_min,
            "price_max": price_max,
            "distance_min": distance_min,
            "distance_max": distance_max,
            "distance_type": distance_type,
            "status_colors": [CargoStatusColor(color) for color in status_colors] if status_colors else None,
            "source": source,
            "is_hidden": is_hidden,
            "order_by": order_by,
            "order_direction": order_direction,
            "page": page,
            "limit": limit
        }

        # Выполняем фильтрацию
        result = use_case.execute(
            vehicle_body_type=vehicle_body_type,
            vehicle_max_weight=vehicle_max_weight,
            vehicle_capacity=vehicle_capacity,
            vehicle_length=vehicle_length,
            vehicle_width=vehicle_width,
            vehicle_height=vehicle_height,
            fuel_consumption=fuel_consumption,
            fuel_price=fuel_price,
            depreciation_per_km=depreciation_per_km,
            driver_salary_per_km=driver_salary_per_km,
            other_costs_per_km=other_costs_per_km,
            empty_run_distance=empty_run_distance,
            **search_params
        )

        # Преобразуем результат в схему ответа
        return SearchCargoResponse(
            items=result.items,
            total=result.total,
            page=result.page,
            limit=result.limit,
            total_pages=result.total_pages
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal server error")


def _parse_date(date_str: Optional[str]) -> Optional[date]:
    """Парсит строку даты в объект date."""
    if not date_str:
        return None
    try:
        from datetime import datetime
        return datetime.strptime(date_str, "%Y-%m-%d").date()
    except ValueError:
        raise ValueError(f"Invalid date format: {date_str}. Use YYYY-MM-DD")