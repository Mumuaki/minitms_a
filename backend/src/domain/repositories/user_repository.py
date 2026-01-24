"""
Интерфейс репозитория пользователей (Domain Layer).
"""
from abc import ABC, abstractmethod
from typing import Optional
from backend.src.domain.entities.user import User

class UserRepository(ABC):
    """Абстрактный класс репозитория пользователей."""
    
    @abstractmethod
    def get_by_email(self, email: str) -> Optional[User]:
        """Получить пользователя по email."""
        pass
    
    @abstractmethod
    def get_by_id(self, user_id: int) -> Optional[User]:
        """Получить пользователя по ID."""
        pass
        
    @abstractmethod
    def create(self, user: User) -> User:
        """Создать нового пользователя."""
        pass
    
    @abstractmethod
    def save(self, user: User) -> User:
        """Сохранить изменения пользователя."""
        pass

    @abstractmethod
    def get_all(self, skip: int = 0, limit: int = 100) -> list[User]:
        """Получить список пользователей."""
        pass

    @abstractmethod
    def delete(self, user: User) -> None:
        """Удалить пользователя."""
        pass
