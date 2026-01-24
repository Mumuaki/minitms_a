"""
Use Case: LoginUser (UC-AUTH-01)

Бизнес-логика входа в систему:
1. Получение пользователя по email
2. Проверка активности и блокировки аккаунта
3. Проверка пароля
4. Генерация JWT токенов
"""

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Optional

from backend.src.application.ports.user_repository_protocol import UserRepositoryProtocol
from backend.src.infrastructure.security.password_hasher import verify_password
from backend.src.infrastructure.security.jwt_handler import (
    create_access_token,
    create_refresh_token,
)

# Попытка импорта UTC из разных версий Python
try:
    from datetime import UTC
except ImportError:
    from datetime import timezone
    UTC = timezone.utc


# Константы для блокировки (FR-AUTH-003)
MAX_FAILED_ATTEMPTS = 5
LOCKOUT_DURATION_MINUTES = 15


@dataclass
class LoginResult:
    """
    Результат попытки входа в систему.
    
    success: True если вход успешен.
    access_token: JWT access token (если успешно).
    refresh_token: JWT refresh token (если успешно).
    error: Сообщение об ошибке (если неуспешно).
    user_id: ID пользователя (если успешно).
    role: Роль пользователя (если успешно).
    """
    success: bool
    access_token: Optional[str] = None
    refresh_token: Optional[str] = None
    error: Optional[str] = None
    user_id: Optional[int] = None
    role: Optional[str] = None


class LoginUserUseCase:
    """
    Use Case для входа пользователя в систему.
    
    Реализует UC-AUTH-01 из спецификации.
    """
    
    def __init__(self, user_repo: UserRepositoryProtocol):
        """
        Args:
            user_repo: Репозиторий пользователей (реализация протокола).
        """
        self._user_repo = user_repo
    
    def execute(
        self,
        email: str,
        password: str,
        remember_me: bool = False
    ) -> LoginResult:
        """
        Выполнить вход в систему.
        
        Args:
            email: Email пользователя.
            password: Пароль в открытом виде.
            remember_me: Если True, refresh token живёт 30 дней.
            
        Returns:
            LoginResult с токенами или ошибкой.
        """
        # 1. Получаем пользователя по email
        user = self._user_repo.get_by_email(email.lower())
        
        if user is None:
            return LoginResult(success=False, error="Incorrect email or password")
        
        # 2. Проверяем активность аккаунта
        if not user.is_active:
            return LoginResult(success=False, error="Account is disabled")
        
        # 3. Проверяем блокировку
        if user.is_locked():
            return LoginResult(success=False, error="Account is locked. Try again later.")
        
        # 4. Проверяем пароль
        if not verify_password(password, user.password_hash):
            # Увеличиваем счётчик неудачных попыток
            self._handle_failed_attempt(user)
            return LoginResult(success=False, error="Incorrect email or password")
        
        # 5. Сбрасываем счётчик неудачных попыток (успешный вход)
        user.reset_failed_attempts()
        self._user_repo.update(user)
        
        # 6. Генерируем токены
        access_token = create_access_token(
            user_id=user.id,
            role=user.role.value
        )
        refresh_token = create_refresh_token(
            user_id=user.id,
            remember_me=remember_me
        )
        
        return LoginResult(
            success=True,
            access_token=access_token,
            refresh_token=refresh_token,
            user_id=user.id,
            role=user.role.value,
        )
    
    def _handle_failed_attempt(self, user) -> None:
        """
        Обрабатывает неудачную попытку входа.
        
        Увеличивает счётчик, блокирует при превышении лимита.
        """
        user.increment_failed_attempts()
        
        # Блокируем если превышен лимит
        if user.failed_login_attempts >= MAX_FAILED_ATTEMPTS:
            user.locked_until = datetime.now(UTC) + timedelta(minutes=LOCKOUT_DURATION_MINUTES)
        
        self._user_repo.update(user)
