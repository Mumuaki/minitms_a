"""
Auth Endpoints — REST API для авторизации.

Эндпоинты:
- POST /auth/login — вход в систему
- POST /auth/refresh — обновление токена
- GET /auth/me — профиль текущего пользователя

ВАЖНО: Теперь используется UserRepository (п.1.5).
"""

from datetime import datetime, timedelta
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
    response: Response,
    form_data: OAuth2PasswordRequestForm = Depends(),
    user_repo: UserRepository = Depends(get_user_repository)
) -> TokenResponse:
    """
    Вход в систему (UC-AUTH-01).
    
    Принимает форму OAuth2 (username = email, password).
    Возвращает пару JWT токенов.
    """
    # #region agent log
    import traceback
    import json
    _log_path = "/app/.cursor/debug.log"
    try:
        import os
        _alt = os.path.join(os.path.dirname(__file__), "../../../../../.cursor/debug.log")
        if os.path.exists(os.path.dirname(_alt)) or os.path.exists("d:/MiniTMS/.cursor"):
            _log_path = "d:/MiniTMS/.cursor/debug.log" if os.name == "nt" else _alt
    except Exception:
        pass
    def _agent_log(msg: str, data: dict, h: str):
        try:
            import os
            _d = os.path.dirname(_log_path)
            if _d:
                os.makedirs(_d, exist_ok=True)
            with open(_log_path, "a", encoding="utf-8") as f:
                f.write(json.dumps({"location": "auth.py:login", "message": msg, "data": data, "hypothesisId": h, "timestamp": __import__("time").time() * 1000}) + "\n")
        except Exception:
            pass
    _agent_log("login_start", {"username_len": len(form_data.username or ""), "password_len": len(form_data.password or "")}, "A")
    # #endregion
    try:
        # Получаем пользователя по email (username в OAuth2 форме)
        user = user_repo.get_by_email(form_data.username)
        _agent_log("get_by_email_done", {"user_found": user is not None, "user_id": user.id if user else None}, "A")
    
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
    
        _agent_log("verify_active", {"is_active": user.is_active}, "B")
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Account is disabled",
                headers={"WWW-Authenticate": "Bearer"},
            )
            
        if user.is_locked():
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Account is locked due to too many failed attempts. Try again later.",
                headers={"WWW-Authenticate": "Bearer"},
            )
    
        _agent_log("verify_password_start", {}, "B")
        if not verify_password(form_data.password, user.password_hash):
            user.increment_failed_attempts()
            if user.failed_login_attempts >= 5:
                user.locked_until = datetime.now() + timedelta(minutes=15)
            user_repo.save(user)
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
            
        # Успешный вход
        user.reset_failed_attempts()
        user_repo.save(user)
    
        role_value = user.role.value if hasattr(user.role, 'value') else user.role
        _agent_log("create_tokens_start", {"role_value": str(role_value)}, "C")
        access_token = create_access_token(user_id=user.id, role=role_value)
        refresh_token_val = create_refresh_token(user_id=user.id, remember_me=False)
        _agent_log("create_tokens_done", {}, "C")
        
        # Устанавливаем refresh token в httpOnly cookie
        response.set_cookie(
            key="refresh_token",
            value=refresh_token_val,
            httponly=True,
            max_age=30 * 24 * 60 * 60, # 30 дней
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
        _agent_log("login_exception", {"error": str(e), "type": type(e).__name__, "traceback": traceback.format_exc()}, "E")
        raise


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
