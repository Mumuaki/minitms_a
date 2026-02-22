"""
JWT Handler - утилита для работы с JWT токенами.

Отвечает за создание и валидацию Access/Refresh токенов.
Согласно спецификации:
- Access Token: 15 минут
- Refresh Token: 30 дней (при "Запомнить меня")
- Алгоритм: HS256 (симметричный)
"""

from datetime import datetime, timedelta
from typing import Optional

from jose import jwt, JWTError

# Попытка импорта UTC из разных версий Python
try:
    from datetime import UTC
except ImportError:
    from datetime import timezone
    UTC = timezone.utc


# Настройки JWT (в продакшене должны браться из переменных окружения)
# TODO: Перенести в config после создания модуля настроек
SECRET_KEY = "your-secret-key-change-in-production"  # Заменить в .env
ALGORITHM = "HS256"

# Время жизни токенов (в минутах)
ACCESS_TOKEN_EXPIRE_MINUTES = 15
REFRESH_TOKEN_EXPIRE_DAYS = 30


def create_access_token(
    user_id: int,
    role: str,
    expires_delta: Optional[timedelta] = None
) -> str:
    """
    Создаёт Access Token для пользователя.
    
    Args:
        user_id: ID пользователя.
        role: Роль пользователя (administrator, director, dispatcher, observer).
        expires_delta: Опциональное время жизни токена.
        
    Returns:
        JWT токен в виде строки.
        
    Example:
        >>> token = create_access_token(user_id=1, role="dispatcher")
        >>> token.count(".") == 2  # JWT имеет 3 части
        True
    """
    # Время истечения
    now = datetime.now(UTC)
    if expires_delta:
        expire = now + expires_delta
    else:
        expire = now + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    # Payload токена (iat/exp должны быть Unix timestamp, не datetime)
    claims = {
        "sub": str(user_id),  # Subject - ID пользователя
        "role": role,
        "type": "access",
        "iat": int(now.timestamp()),
        "exp": int(expire.timestamp()),
    }
    
    token = jwt.encode(claims, SECRET_KEY, algorithm=ALGORITHM)
    return token if isinstance(token, str) else token.decode("utf-8")


def create_refresh_token(
    user_id: int,
    remember_me: bool = False
) -> str:
    """
    Создаёт Refresh Token для пользователя.
    
    Args:
        user_id: ID пользователя.
        remember_me: Если True, токен живёт 30 дней, иначе 1 день.
        
    Returns:
        JWT токен в виде строки.
    """
    # Время жизни зависит от флага "Запомнить меня"
    now = datetime.now(UTC)
    if remember_me:
        expire = now + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    else:
        expire = now + timedelta(days=1)
    
    # Payload токена (iat/exp должны быть Unix timestamp, не datetime)
    claims = {
        "sub": str(user_id),
        "type": "refresh",
        "iat": int(now.timestamp()),
        "exp": int(expire.timestamp()),
    }
    
    token = jwt.encode(claims, SECRET_KEY, algorithm=ALGORITHM)
    return token if isinstance(token, str) else token.decode("utf-8")


def decode_token(token: str) -> dict:
    """
    Декодирует и валидирует JWT токен.
    
    Args:
        token: JWT токен для декодирования.
        
    Returns:
        Словарь с данными из токена (payload).
        
    Raises:
        JWTError: Если токен невалидный или истёк.
        
    Example:
        >>> token = create_access_token(user_id=1, role="admin")
        >>> payload = decode_token(token)
        >>> payload["sub"]
        '1'
    """
    return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])


def get_user_id_from_token(token: str) -> Optional[int]:
    """
    Извлекает user_id из токена.
    
    Args:
        token: JWT токен.
        
    Returns:
        ID пользователя или None если токен невалидный.
    """
    try:
        payload = decode_token(token)
        user_id = payload.get("sub")
        if user_id is None:
            return None
        return int(user_id)
    except (JWTError, ValueError):
        return None


def get_token_type(token: str) -> Optional[str]:
    """
    Возвращает тип токена (access или refresh).
    
    Args:
        token: JWT токен.
        
    Returns:
        Тип токена или None если токен невалидный.
    """
    try:
        payload = decode_token(token)
        return payload.get("type")
    except JWTError:
        return None
