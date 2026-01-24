"""
Auth Endpoints — REST API для авторизации.

Эндпоинты:
- POST /auth/login — вход в систему
- POST /auth/refresh — обновление токена
- GET /auth/me — профиль текущего пользователя

ВАЖНО: Теперь используется UserRepository (п.1.5).
"""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from jose import JWTError
from sqlalchemy.orm import Session

from backend.src.infrastructure.security.jwt_handler import (
    create_access_token,
    create_refresh_token,
    decode_token,
)
from backend.src.infrastructure.security.password_hasher import verify_password
from backend.src.infrastructure.api.v1.schemas.auth_schema import (
    RefreshRequest,
    TokenResponse,
    UserResponse,
    ErrorResponse,
)
from backend.src.infrastructure.api.v1.dependencies import (
    get_current_user,
    CurrentUser,
)
from backend.src.infrastructure.persistence.sqlalchemy.database import get_db
from backend.src.domain.repositories.user_repository import UserRepository
from backend.src.infrastructure.persistence.sqlalchemy.repositories.user_repository import SqlAlchemyUserRepository


# Роутер с префиксом /auth
router = APIRouter(prefix="/auth", tags=["Authentication"])


# ============================================================================
# DEPENDENCIES
# ============================================================================

def get_user_repository(db: Session = Depends(get_db)) -> UserRepository:
    """Dependency для получения репозитория пользователей."""
    return SqlAlchemyUserRepository(db)


# ============================================================================
# ENDPOINTS
# ============================================================================

@router.post(
    "/login",
    response_model=TokenResponse,
    responses={401: {"model": ErrorResponse}},
    summary="Вход в систему",
    description="Аутентификация по email и паролю. Возвращает access и refresh токены.",
)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    user_repo: UserRepository = Depends(get_user_repository)
) -> TokenResponse:
    """
    Вход в систему (UC-AUTH-01).
    
    Принимает форму OAuth2 (username = email, password).
    Возвращает пару JWT токенов.
    """
    # Получаем пользователя по email (username в OAuth2 форме)
    user = user_repo.get_by_email(form_data.username)
    
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Проверяем активность аккаунта
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Account is disabled",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Проверяем пароль
    if not verify_password(form_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Генерируем токены
    role_value = user.role.value if hasattr(user.role, 'value') else user.role
    
    access_token = create_access_token(user_id=user.id, role=role_value)
    refresh_token = create_refresh_token(user_id=user.id, remember_me=False)
    
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
    )


@router.post(
    "/refresh",
    response_model=TokenResponse,
    responses={401: {"model": ErrorResponse}},
    summary="Обновление токена",
    description="Обновляет access token по refresh token.",
)
async def refresh_token(
    request: RefreshRequest,
    user_repo: UserRepository = Depends(get_user_repository)
) -> TokenResponse:
    """
    Обновление токена доступа.
    
    Принимает refresh_token, возвращает новую пару токенов.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid refresh token",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = decode_token(request.refresh_token)
        
        # Проверяем тип токена
        if payload.get("type") != "refresh":
            raise credentials_exception
        
        user_id_str = payload.get("sub")
        if user_id_str is None:
            raise credentials_exception
        
        user_id = int(user_id_str)
        
    except (JWTError, ValueError):
        raise credentials_exception
    
    # Получаем пользователя для получения роли
    user = user_repo.get_by_id(user_id)
    if user is None or not user.is_active:
        raise credentials_exception
    
    # Генерируем новые токены
    role_value = user.role.value if hasattr(user.role, 'value') else user.role
    
    access_token = create_access_token(user_id=user.id, role=role_value)
    new_refresh_token = create_refresh_token(user_id=user.id, remember_me=False)
    
    return TokenResponse(
        access_token=access_token,
        refresh_token=new_refresh_token,
        token_type="bearer",
    )


@router.get(
    "/me",
    response_model=UserResponse,
    responses={401: {"model": ErrorResponse}},
    summary="Профиль текущего пользователя",
    description="Возвращает данные авторизованного пользователя.",
)
async def get_me(
    current_user: CurrentUser = Depends(get_current_user),
    user_repo: UserRepository = Depends(get_user_repository)
) -> UserResponse:
    """
    Получение профиля текущего пользователя.
    
    Требует авторизации (Bearer token).
    """
    # Получаем полные данные пользователя
    user = user_repo.get_by_id(current_user.id)
    
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    
    role_value = user.role.value if hasattr(user.role, 'value') else user.role
    
    return UserResponse(
        id=user.id,
        email=user.email,
        username=user.username,
        role=role_value,
        language=user.language,
        is_active=user.is_active,
    )
