"""
SQLAlchemy реализация UserRepository.

Реализует UserRepositoryProtocol для работы с PostgreSQL.
"""

from typing import Optional
from sqlalchemy.orm import Session

from backend.src.domain.entities.user import User


class UserRepository:
    """
    SQLAlchemy реализация репозитория пользователей.
    
    Реализует UserRepositoryProtocol из application/ports.
    """
    
    def __init__(self, session: Session):
        """
        Args:
            session: SQLAlchemy сессия.
        """
        self._session = session
    
    def get_by_email(self, email: str) -> Optional[User]:
        """
        Получить пользователя по email.
        
        Args:
            email: Email пользователя (case-insensitive).
            
        Returns:
            User если найден, None если нет.
        """
        return self._session.query(User).filter(
            User.email == email.lower()
        ).first()
    
    def get_by_id(self, user_id: int) -> Optional[User]:
        """
        Получить пользователя по ID.
        
        Args:
            user_id: ID пользователя.
            
        Returns:
            User если найден, None если нет.
        """
        return self._session.query(User).filter(
            User.id == user_id
        ).first()
    
    def create(self, user: User) -> User:
        """
        Создать нового пользователя.
        
        Args:
            user: Объект User для создания.
            
        Returns:
            Созданный User с присвоенным ID.
        """
        self._session.add(user)
        self._session.commit()
        self._session.refresh(user)
        return user
    
    def update(self, user: User) -> None:
        """
        Обновить данные пользователя.
        
        Args:
            user: Обновлённый объект User.
        """
        self._session.commit()
    
    def delete(self, user: User) -> None:
        """
        Удалить пользователя.
        
        Args:
            user: Пользователь для удаления.
        """
        self._session.delete(user)
        self._session.commit()
    
    def exists_by_email(self, email: str) -> bool:
        """
        Проверить существование пользователя по email.
        
        Args:
            email: Email для проверки.
            
        Returns:
            True если пользователь существует.
        """
        return self._session.query(User).filter(
            User.email == email.lower()
        ).count() > 0
