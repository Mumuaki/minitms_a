"""
FastAPI Dependencies для авторизации.

Предоставляет:
- oauth2_scheme — схема OAuth2 Bearer
- get_current_user — получение текущего пользователя из токена
- require_role — фабрика зависимостей для проверки ролей
- get_user_repository — получение репозитория пользователей
"""

from typing import Optional, List, Callable
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError
from sqlalchemy.orm import Session

from backend.src.infrastructure.security.jwt_handler import decode_token, get_token_type
from backend.src.infrastructure.security.rbac import has_permission, Permission

from backend.src.infrastructure.persistence.sqlalchemy.database import get_db
from backend.src.domain.repositories.user_repository import UserRepository
from backend.src.infrastructure.persistence.sqlalchemy.repositories.user_repository import SqlAlchemyUserRepository
from backend.src.domain.repositories.cargo_repository import CargoRepository
from backend.src.infrastructure.persistence.sqlalchemy.repositories.cargo_repository_impl import CargoRepositoryImpl
from backend.src.domain.repositories.vehicle_repository import VehicleRepository
from backend.src.infrastructure.persistence.sqlalchemy.repositories.vehicle_repository_impl import VehicleRepositoryImpl
from backend.src.application.ports.maps_port import MapsPort
from backend.src.infrastructure.external_services.osrm.adapter import OSRMMapsAdapter
from backend.src.domain.services.route_optimizer import RouteOptimizer
from backend.src.domain.services.profitability_calculator import ProfitabilityCalculator
from backend.src.domain.services.route_planner import RoutePlanner
from backend.src.application.use_cases.plan_routes import PlanRoutesUseCase


# OAuth2 схема — указывает FastAPI где находится endpoint логина
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


class CurrentUser:
    """
    Данные текущего пользователя из токена.
    
    Используется как результат get_current_user dependency.
    """
    def __init__(self, user_id: int, role: str):
        self.id = user_id
        self.role = role
    
    def __repr__(self) -> str:
        return f"<CurrentUser(id={self.id}, role='{self.role}')>"


async def get_current_user(token: str = Depends(oauth2_scheme)) -> CurrentUser:
    """
    Dependency для получения текущего пользователя.
    
    Декодирует JWT токен и возвращает данные пользователя.
    
    Args:
        token: JWT токен из заголовка Authorization.
        
    Returns:
        CurrentUser с id и role.
        
    Raises:
        HTTPException 401: Если токен невалидный или истёк.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = decode_token(token)
        
        # Проверяем тип токена — должен быть access
        token_type = payload.get("type")
        if token_type != "access":
            raise credentials_exception
        
        # Извлекаем user_id и role
        user_id_str = payload.get("sub")
        role = payload.get("role")
        
        if user_id_str is None or role is None:
            raise credentials_exception
            
        user_id = int(user_id_str)
        
    except (JWTError, ValueError):
        raise credentials_exception
    
    return CurrentUser(user_id=user_id, role=role)


def require_role(allowed_roles: List[str]) -> Callable:
    """
    Фабрика dependency для проверки роли пользователя.
    """
    async def role_checker(current_user: CurrentUser = Depends(get_current_user)) -> CurrentUser:
        # Приводим к нижнему регистру для сравнения, если в Enum значения lowercase
        user_role = current_user.role.lower() if isinstance(current_user.role, str) else current_user.role.value.lower()
        allowed = [r.lower() for r in allowed_roles]
        
        if user_role not in allowed:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role '{user_role}' is not allowed. Required: {allowed}"
            )
        return current_user
    
    return role_checker


def require_permission(permission: Permission) -> Callable:
    """
    Фабрика dependency для проверки конкретного разрешения.
    """
    async def permission_checker(current_user: CurrentUser = Depends(get_current_user)) -> CurrentUser:
        if not has_permission(current_user.role, permission):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission '{permission.value}' is required"
            )
        return current_user
    
    return permission_checker


def get_user_repository(db: Session = Depends(get_db)) -> UserRepository:
    """Dependency для получения репозитория пользователей."""
    return SqlAlchemyUserRepository(db)


def get_cargo_repository(db: Session = Depends(get_db)) -> CargoRepository:
    """Dependency для получения репозитория грузов."""
    return CargoRepositoryImpl(db)


def get_vehicle_repository(db: Session = Depends(get_db)) -> VehicleRepository:
    """Dependency для получения репозитория транспортных средств."""
    return VehicleRepositoryImpl(db)


def get_maps_service() -> MapsPort:
    """Dependency для получения сервиса карт."""
    return OSRMMapsAdapter()


def get_route_optimizer(maps_service: MapsPort = Depends(get_maps_service)) -> RouteOptimizer:
    """Dependency для получения оптимизатора маршрутов."""
    return RouteOptimizer(maps_service)


def get_profitability_calculator() -> ProfitabilityCalculator:
    """Dependency для получения калькулятора рентабельности."""
    return ProfitabilityCalculator()


def get_route_planner(
    route_optimizer: RouteOptimizer = Depends(get_route_optimizer),
    profitability_calculator: ProfitabilityCalculator = Depends(get_profitability_calculator),
    cargo_repo: CargoRepository = Depends(get_cargo_repository),
    vehicle_repo: VehicleRepository = Depends(get_vehicle_repository)
) -> RoutePlanner:
    """Dependency для получения планировщика маршрутов."""
    return RoutePlanner(
        route_optimizer=route_optimizer,
        profitability_calculator=profitability_calculator,
        cargo_repository=cargo_repo,
        vehicle_repository=vehicle_repo
    )


def get_plan_routes_use_case(
    route_planner: RoutePlanner = Depends(get_route_planner)
) -> PlanRoutesUseCase:
    """Dependency для получения use case планирования маршрутов."""
    return PlanRoutesUseCase(route_planner)
