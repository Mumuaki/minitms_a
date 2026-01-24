"""
Протокол репозитория пользователей.

Определяет контракт для работы с пользователями, который должен быть
реализован инфраструктурным слоем (например, SQLAlchemy репозиторий).
"""

from typing import Protocol, Optional

from backend.src.domain.entities.user import User


class UserRepositoryProtocol(Protocol):
    """
    Протокол (интерфейс) для репозитория пользователей.
    
    Use Cases зависят от этого протокола, а не от конкретной реализации.
    Это позволяет:
    - Подменять реализацию (mock, SQLAlchemy, etc.)
    - Тестировать Use Cases изолированно
    """
    
    def get_by_email(self, email: str) -> Optional[User]:
        """
        Получить пользователя по email.
        
        Args:
            email: Email пользователя.
            
        Returns:
            User если найден, None если нет.
        """
        ...
    
    def get_by_id(self, user_id: int) -> Optional[User]:
        """
        Получить пользователя по ID.
        
        Args:
            user_id: ID пользователя.
            
        Returns:
            User если найден, None если нет.
        """
        ...
    
    def update(self, user: User) -> None:
        """
        Обновить данные пользователя.
        
        Args:
            user: Обновлённый объект пользователя.
        """
        ...
