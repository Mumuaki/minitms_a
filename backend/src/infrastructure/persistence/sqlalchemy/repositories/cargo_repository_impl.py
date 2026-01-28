"""
SQLAlchemy реализация CargoRepository.

Реализует CargoRepository для работы с PostgreSQL.
"""

from typing import Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc, asc

from backend.src.domain.repositories.cargo_repository import CargoRepository
from backend.src.application.dto.cargo_dto import (
    SearchCargoRequestDto,
    SearchCargoResponseDto,
    CargoDto,
    LocationDto,
    ProfitabilityDto,
    CargoStatusColor
)
from backend.src.infrastructure.persistence.sqlalchemy.models.cargo_model import Cargo


class CargoRepositoryImpl(CargoRepository):
    """
    SQLAlchemy реализация репозитория грузов.
    """

    def __init__(self, session: Session):
        """
        Args:
            session: SQLAlchemy сессия.
        """
        self._session = session

    def search_cargos(self, request: SearchCargoRequestDto) -> SearchCargoResponseDto:
        """
        Поиск грузов с фильтрами, сортировкой и пагинацией.

        Args:
            request: Параметры поиска.

        Returns:
            SearchCargoResponseDto с результатами.
        """
        query = self._session.query(Cargo)

        # Применяем фильтры
        query = self._apply_filters(query, request)

        # Получаем общее количество для пагинации
        total = query.count()

        # Применяем сортировку
        query = self._apply_ordering(query, request)

        # Применяем пагинацию
        offset = (request.page - 1) * request.limit
        query = query.offset(offset).limit(request.limit)

        # Получаем результаты
        cargo_models = query.all()
        items = [self._model_to_dto(cargo) for cargo in cargo_models]

        # Вычисляем общее количество страниц
        total_pages = (total + request.limit - 1) // request.limit

        return SearchCargoResponseDto(
            items=items,
            total=total,
            page=request.page,
            limit=request.limit,
            total_pages=total_pages
        )

    def _apply_filters(self, query, request: SearchCargoRequestDto):
        """Применяет фильтры к запросу."""
        filters = []

        # Фильтр по дате загрузки
        if request.loading_date_from:
            filters.append(Cargo.loading_date >= request.loading_date_from)
        if request.loading_date_to:
            filters.append(Cargo.loading_date <= request.loading_date_to)

        # Фильтр по дате выгрузки
        if request.unloading_date_from:
            filters.append(Cargo.unloading_date >= request.unloading_date_from)
        if request.unloading_date_to:
            filters.append(Cargo.unloading_date <= request.unloading_date_to)

        # Фильтр по весу
        if request.weight_min is not None:
            filters.append(Cargo.weight >= request.weight_min)
        if request.weight_max is not None:
            filters.append(Cargo.weight <= request.weight_max)

        # Фильтр по типу кузова
        if request.body_type:
            filters.append(Cargo.body_type == request.body_type)

        # Фильтр по цене
        if request.price_min is not None:
            filters.append(Cargo.price >= request.price_min)
        if request.price_max is not None:
            filters.append(Cargo.price <= request.price_max)

        # Фильтр по расстоянию
        distance_field = (Cargo.distance_trans_eu if request.distance_type == "trans_eu"
                         else Cargo.distance_osm)
        if request.distance_min is not None:
            filters.append(distance_field >= request.distance_min)
        if request.distance_max is not None:
            filters.append(distance_field <= request.distance_max)

        # Фильтр по статусу цвета
        if request.status_colors:
            filters.append(Cargo.status_color.in_(request.status_colors))

        # Фильтр по источнику
        if request.source:
            filters.append(Cargo.source == request.source)

        # Фильтр по скрытым
        if request.is_hidden is not None:
            filters.append(Cargo.is_hidden == request.is_hidden)

        # Фильтры по транспортному средству
        if request.vehicle_body_type:
            # Предполагаем, что тип кузова должен совпадать или быть совместимым
            # Для простоты: точное совпадение
            filters.append(Cargo.body_type == request.vehicle_body_type)

        if request.vehicle_max_weight is not None:
            # Вес груза не должен превышать максимальный вес ТС
            filters.append(Cargo.weight <= request.vehicle_max_weight)

        # Другие фильтры по ТС (габариты, вместимость) можно добавить, если поля будут в модели

        if filters:
            query = query.filter(and_(*filters))

        return query

    def _apply_ordering(self, query, request: SearchCargoRequestDto):
        """Применяет сортировку к запросу."""
        order_field = getattr(Cargo, request.order_by)
        if request.order_direction == "desc":
            query = query.order_by(desc(order_field))
        else:
            query = query.order_by(asc(order_field))
        return query

    def _model_to_dto(self, cargo: Cargo) -> CargoDto:
        """Преобразует модель в DTO."""
        return CargoDto(
            id=str(cargo.id),
            external_id=cargo.external_id,
            source=cargo.source,
            loading_place=LocationDto(**cargo.loading_place),
            unloading_place=LocationDto(**cargo.unloading_place),
            loading_date=cargo.loading_date,
            unloading_date=cargo.unloading_date,
            weight=cargo.weight,
            body_type=cargo.body_type,
            price=cargo.price,
            distance_trans_eu=cargo.distance_trans_eu,
            distance_osm=cargo.distance_osm,
            is_hidden=cargo.is_hidden,
            created_at=cargo.created_at.isoformat()
        )

    def get_by_id(self, cargo_id: str) -> Optional[CargoDto]:
        """Получить груз по ID."""
        cargo = self._session.query(Cargo).filter(Cargo.id == cargo_id).first()
        return self._model_to_dto(cargo) if cargo else None

    def get_by_external_id(self, external_id: str) -> Optional[CargoDto]:
        """Получить груз по внешнему ID."""
        cargo = self._session.query(Cargo).filter(Cargo.external_id == external_id).first()
        return self._model_to_dto(cargo) if cargo else None

    def create(self, cargo_dto: CargoDto) -> CargoDto:
        """Создать новый груз."""
        # Преобразование DTO в модель
        cargo = Cargo(
            external_id=cargo_dto.external_id,
            source=cargo_dto.source,
            loading_place=cargo_dto.loading_place.dict(),
            unloading_place=cargo_dto.unloading_place.dict(),
            loading_date=cargo_dto.loading_date,
            unloading_date=cargo_dto.unloading_date,
            weight=cargo_dto.weight,
            body_type=cargo_dto.body_type,
            price=cargo_dto.price,
            distance_trans_eu=cargo_dto.distance_trans_eu,
            distance_osm=cargo_dto.distance_osm,
            rate_per_km=cargo_dto.rate_per_km,
            total_cost=cargo_dto.total_cost,
            status_color=cargo_dto.status_color,
            is_hidden=cargo_dto.is_hidden
        )
        self._session.add(cargo)
        self._session.commit()
        self._session.refresh(cargo)
        return self._model_to_dto(cargo)

    def update(self, cargo_dto: CargoDto) -> CargoDto:
        """Обновить груз."""
        cargo = self._session.query(Cargo).filter(Cargo.id == cargo_dto.id).first()
        if not cargo:
            raise ValueError(f"Cargo with id {cargo_dto.id} not found")

        # Обновляем поля
        cargo.external_id = cargo_dto.external_id
        cargo.source = cargo_dto.source
        cargo.loading_place = cargo_dto.loading_place.dict()
        cargo.unloading_place = cargo_dto.unloading_place.dict()
        cargo.loading_date = cargo_dto.loading_date
        cargo.unloading_date = cargo_dto.unloading_date
        cargo.weight = cargo_dto.weight
        cargo.body_type = cargo_dto.body_type
        cargo.price = cargo_dto.price
        cargo.distance_trans_eu = cargo_dto.distance_trans_eu
        cargo.distance_osm = cargo_dto.distance_osm
        cargo.rate_per_km = cargo_dto.rate_per_km
        cargo.total_cost = cargo_dto.total_cost
        cargo.status_color = cargo_dto.status_color
        cargo.is_hidden = cargo_dto.is_hidden

        self._session.commit()
        return self._model_to_dto(cargo)

    def delete(self, cargo_id: str) -> None:
        """Удалить груз."""
        cargo = self._session.query(Cargo).filter(Cargo.id == cargo_id).first()
        if cargo:
            self._session.delete(cargo)
            self._session.commit()