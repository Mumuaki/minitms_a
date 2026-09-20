"""
Auth Endpoints — REST API для авторизации.

Эндпоинты:
- POST /auth/login — вход в систему
- POST /auth/refresh — обновление токена
- GET /auth/me — профиль текущего пользователя

ВАЖНО: Теперь используется UserRepository (п.1.5).
"""

from datetime import datetime, timedelta
from typing import List, Optional
from collections import defaultdict, deque
from pydantic import BaseModel
from fastapi import APIRouter, Depends, HTTPException, status, Response, Request
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
    TokenResponse,
    UserResponse,
    ErrorResponse,
)
from backend.src.infrastructure.api.v1.dependencies import (
    get_current_user,
    CurrentUser,
    require_role,
)
from backend.src.infrastructure.persistence.sqlalchemy.database import get_db
from backend.src.domain.repositories.user_repository import UserRepository
from backend.src.infrastructure.persistence.sqlalchemy.repositories.user_repository import SqlAlchemyUserRepository
from backend.src.domain.entities.audit_log import AuthAuditLog


# Роутер с префиксом /auth
router = APIRouter(prefix="/auth", tags=["Authentication"])


# ============================================================================
# DEPENDENCIES
# ============================================================================

def get_user_repository(db: Session = Depends(get_db)) -> UserRepository:
    """Dependency для получения репозитория пользователей."""
    return SqlAlchemyUserRepository(db)


_LOGIN_ATTEMPTS = defaultdict(deque)


def _client_ip(request: Request):
    xff = request.headers.get("x-forwarded-for")
    if xff:
        return xff.split(",")[0].strip()
    return request.client.host if request.client else None


def _enforce_login_rate_limit(ip):
    if ip is None:
        return
    now = datetime.now()
    q = _LOGIN_ATTEMPTS[ip]
    while q and (now - q[0]).total_seconds() > 60:
        q.popleft()
    if len(q) >= 10:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many login attempts. Try again in a minute.",
        )
    q.append(now)


def _audit_login(db, email, user_id, ip, user_agent, success):
    db.add(AuthAuditLog(email=email, user_id=user_id, ip=ip, user_agent=user_agent, success=success))
    db.commit()


class AuditLogEntry(BaseModel):
    id: int
    email: str
    ip: Optional[str] = None
    user_agent: Optional[str] = None
    success: bool
    created_at: datetime

    class Config:
        from_attributes = True


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
    response: Response,
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
    user_repo: UserRepository = Depends(get_user_repository),
    db: Session = Depends(get_db),
) -> TokenResponse:
    """
    Вход в систему (UC-AUTH-01).

    Принимает форму OAuth2 (username = email, password).
    Возвращает пару JWT токенов.
    """
    ip = _client_ip(request)
    user_agent = (request.headers.get("user-agent") or "")[:512]
    _enforce_login_rate_limit(ip)
    email = form_data.username
    try:
        user = user_repo.get_by_email(email)

        if user is None:
            _audit_login(db, email=email, user_id=None, ip=ip, user_agent=user_agent, success=False)
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password",
                headers={"WWW-Authenticate": "Bearer"},
            )

        if not user.is_active:
            _audit_login(db, email=email, user_id=user.id, ip=ip, user_agent=user_agent, success=False)
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Account is disabled",
                headers={"WWW-Authenticate": "Bearer"},
            )

        if user.is_locked():
            _audit_login(db, email=email, user_id=user.id, ip=ip, user_agent=user_agent, success=False)
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Account is locked due to too many failed attempts. Try again later.",
                headers={"WWW-Authenticate": "Bearer"},
            )

        if not verify_password(form_data.password, user.password_hash):
            user.increment_failed_attempts()
            if user.failed_login_attempts >= 5:
                user.locked_until = datetime.now() + timedelta(minutes=15)
            user_repo.save(user)
            _audit_login(db, email=email, user_id=user.id, ip=ip, user_agent=user_agent, success=False)
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password",
                headers={"WWW-Authenticate": "Bearer"},
            )

        user.reset_failed_attempts()
        user_repo.save(user)
        _audit_login(db, email=email, user_id=user.id, ip=ip, user_agent=user_agent, success=True)

        role_value = user.role.value if hasattr(user.role, 'value') else user.role
        access_token = create_access_token(user_id=user.id, role=role_value)
        refresh_token_val = create_refresh_token(user_id=user.id, remember_me=False)

        response.set_cookie(
            key="refresh_token",
            value=refresh_token_val,
            httponly=True,
            max_age=30 * 24 * 60 * 60,
            secure=True,
            samesite="lax"
        )

        return TokenResponse(
            access_token=access_token,
            token_type="bearer",
        )
    except HTTPException:
        raise
    except Exception as e:
        raise


@router.get("/audit-log", response_model=List[AuditLogEntry])
async def get_audit_log(
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(require_role(["administrator"])),
):
    """Журнал входов (FR-AUTH-005). Только для администратора."""
    rows = db.query(AuthAuditLog).order_by(AuthAuditLog.created_at.desc()).limit(limit).all()
    return rows


@router.post(
    "/refresh",
    response_model=TokenResponse,
    responses={401: {"model": ErrorResponse}},
    summary="Обновление токена",
    description="Обновляет access token по refresh token.",
)
async def refresh_token(
    request: Request,
    response: Response,
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
    
    refresh_token_val = request.cookies.get("refresh_token")
    if not refresh_token_val:
        raise credentials_exception
        
    try:
        payload = decode_token(refresh_token_val)
        
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
    
    response.set_cookie(
        key="refresh_token",
        value=new_refresh_token,
        httponly=True,
        max_age=30 * 24 * 60 * 60,
        secure=True, 
        samesite="lax"
    )
    
    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
    )

@router.post(
    "/logout",
    summary="Выход из системы",
    description="Удаляет refresh token из кук.",
)
async def logout(response: Response):
    response.delete_cookie("refresh_token")
    return {"status": "success", "message": "Logged out successfully"}


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
