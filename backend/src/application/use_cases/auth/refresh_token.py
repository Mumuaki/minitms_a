"""
Use Case: RefreshToken

Бизнес-логика обновления access token:
1. Декодирование refresh token
2. Проверка пользователя
3. Генерация новой пары токенов
"""

from dataclasses import dataclass
from typing import Optional

from jose import JWTError

from backend.src.application.ports.user_repository_protocol import UserRepositoryProtocol
from backend.src.infrastructure.security.jwt_handler import (
    decode_token,
    create_access_token,
    create_refresh_token,
)


@dataclass
class TokenResult:
    """
    Результат обновления токена.
    
    success: True если обновление успешно.
    access_token: Новый access token (если успешно).
    refresh_token: Новый refresh token (если успешно).
    error: Сообщение об ошибке (если неуспешно).
    """
    success: bool
    access_token: Optional[str] = None
    refresh_token: Optional[str] = None
    error: Optional[str] = None


class RefreshTokenUseCase:
    """
    Use Case для обновления токена доступа.
    
    Принимает refresh token, возвращает новую пару токенов.
    """
    
    def __init__(self, user_repo: UserRepositoryProtocol):
        """
        Args:
            user_repo: Репозиторий пользователей.
        """
        self._user_repo = user_repo
    
    def execute(self, refresh_token: str) -> TokenResult:
        """
        Обновить токен доступа.
        
        Args:
            refresh_token: JWT refresh token.
            
        Returns:
            TokenResult с новыми токенами или ошибкой.
        """
        # 1. Декодируем токен
        try:
            payload = decode_token(refresh_token)
        except JWTError:
            return TokenResult(success=False, error="Invalid refresh token")
        
        # 2. Проверяем тип токена
        if payload.get("type") != "refresh":
            return TokenResult(success=False, error="Invalid token type")
        
        # 3. Извлекаем user_id
        user_id_str = payload.get("sub")
        if user_id_str is None:
            return TokenResult(success=False, error="Invalid token payload")
        
        try:
            user_id = int(user_id_str)
        except ValueError:
            return TokenResult(success=False, error="Invalid user ID in token")
        
        # 4. Получаем пользователя
        user = self._user_repo.get_by_id(user_id)
        
        if user is None:
            return TokenResult(success=False, error="User not found")
        
        if not user.is_active:
            return TokenResult(success=False, error="Account is disabled")
        
        # 5. Генерируем новые токены
        new_access_token = create_access_token(
            user_id=user.id,
            role=user.role.value
        )
        new_refresh_token = create_refresh_token(
            user_id=user.id,
            remember_me=False
        )
        
        return TokenResult(
            success=True,
            access_token=new_access_token,
            refresh_token=new_refresh_token,
        )
