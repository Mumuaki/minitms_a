from typing import Optional, List
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc, asc
from sqlalchemy.dialects.postgresql import insert

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
        # Same as before...
        query = self._session.query(Cargo)
        query = self._apply_filters(query, request)
        total = query.count()
        query = self._apply_ordering(query, request)
        offset = (request.page - 1) * request.limit
        query = query.offset(offset).limit(request.limit)
        cargo_models = query.all()
        items = [self._model_to_dto(cargo) for cargo in cargo_models]
        total_pages = (total + request.limit - 1) // request.limit

        return SearchCargoResponseDto(
            items=items, total=total, page=request.page, limit=request.limit, total_pages=total_pages
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
            filters.append(Cargo.body_type == request.vehicle_body_type)

        if request.vehicle_max_weight is not None:
            filters.append(Cargo.weight <= request.vehicle_max_weight)

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
        return CargoDto(
            id=str(cargo.id),
            external_id=cargo.external_id,
            source=cargo.source,
            loading_place=LocationDto(**cargo.loading_place) if isinstance(cargo.loading_place, dict) else cargo.loading_place,
            unloading_place=LocationDto(**cargo.unloading_place) if isinstance(cargo.unloading_place, dict) else cargo.unloading_place,
            loading_date=cargo.loading_date,
            unloading_date=cargo.unloading_date,
            weight=cargo.weight,
            body_type=cargo.body_type,
            price=cargo.price,
            distance_trans_eu=cargo.distance_trans_eu,
            distance_osm=cargo.distance_osm,
            route_polyline=cargo.route_polyline,
            company_rating=cargo.company_rating,
            published_at=cargo.published_at,
            is_hidden=cargo.is_hidden,
            created_at=cargo.created_at.isoformat()
        )

    def get_by_id(self, cargo_id: str) -> Optional[CargoDto]:
        cargo = self._session.query(Cargo).filter(Cargo.id == cargo_id).first()
        return self._model_to_dto(cargo) if cargo else None

    def get_by_external_id(self, external_id: str) -> Optional[CargoDto]:
        # Возвращаем самую свежую запись по external_id
        cargo = self._session.query(Cargo).filter(
            Cargo.external_id == external_id
        ).order_by(desc(Cargo.snapshot_time_bucket)).first()
        return self._model_to_dto(cargo) if cargo else None

    def create(self, cargo_dto: CargoDto) -> CargoDto:
        return self.upsert(cargo_dto, self._current_bucket())

    def update(self, cargo_dto: CargoDto) -> CargoDto:
        return self.upsert(cargo_dto, self._current_bucket())

    @staticmethod
    def _current_bucket() -> datetime:
        return datetime.now(timezone.utc).replace(minute=0, second=0, microsecond=0)
        
    def upsert(self, cargo_dto: CargoDto, snapshot_time_bucket: datetime) -> CargoDto:
        """PostgreSQL ON CONFLICT DO UPDATE upsert."""
        stmt = insert(Cargo).values(
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
            route_polyline=cargo_dto.route_polyline,
            rate_per_km=cargo_dto.profitability.rate_per_km if cargo_dto.profitability else None,
            total_cost=None,
            status_color=cargo_dto.profitability.color_code if cargo_dto.profitability else CargoStatusColor.GRAY,
            company_rating=cargo_dto.company_rating,
            published_at=cargo_dto.published_at,
            is_hidden=cargo_dto.is_hidden,
            snapshot_time_bucket=snapshot_time_bucket
        )
        
        # Определяем словарь для обновления при конфликте
        update_dict = {
            "loading_place": stmt.excluded.loading_place,
            "unloading_place": stmt.excluded.unloading_place,
            "price": stmt.excluded.price,
            "distance_trans_eu": stmt.excluded.distance_trans_eu,
            "distance_osm": stmt.excluded.distance_osm,
            "route_polyline": stmt.excluded.route_polyline,
            "rate_per_km": stmt.excluded.rate_per_km,
            "status_color": stmt.excluded.status_color,
            "company_rating": stmt.excluded.company_rating,
            "published_at": stmt.excluded.published_at,
            "is_hidden": stmt.excluded.is_hidden
        }
        
        stmt = stmt.on_conflict_do_update(
            index_elements=["source", "external_id", "snapshot_time_bucket"],
            set_=update_dict
        ).returning(Cargo)
        
        result = self._session.execute(stmt)
        cargo = result.scalar_one()
        self._session.commit()
        return self._model_to_dto(cargo)

    def delete(self, cargo_id: str) -> None:
        cargo = self._session.query(Cargo).filter(Cargo.id == cargo_id).first()
        if cargo:
            self._session.delete(cargo)
            self._session.commit()
