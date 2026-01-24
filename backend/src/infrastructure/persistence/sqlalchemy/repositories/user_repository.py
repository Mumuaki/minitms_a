"""
SQLAlchemy реализация репозитория пользователей (Infrastructure Layer).
"""
from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import select

from backend.src.domain.repositories.user_repository import UserRepository
from backend.src.domain.entities.user import User

class SqlAlchemyUserRepository(UserRepository):
    """
    Реализация репозитория пользователей с использованием SQLAlchemy.
    """
    
    def __init__(self, db: Session):
        self.db = db
        
    def get_by_email(self, email: str) -> Optional[User]:
        """Получить пользователя по email."""
        stmt = select(User).where(User.email == email.lower())
        return self.db.execute(stmt).scalar_one_or_none()
    
    def get_by_id(self, user_id: int) -> Optional[User]:
        """Получить пользователя по ID."""
        stmt = select(User).where(User.id == user_id)
        return self.db.execute(stmt).scalar_one_or_none()
        
    def create(self, user: User) -> User:
        """Создать нового пользователя."""
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user
        
    def save(self, user: User) -> User:
        """Сохранить изменения (update)."""
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user
        
    def get_all(self, skip: int = 0, limit: int = 100) -> list[User]:
        """Получить список пользователей."""
        stmt = select(User).offset(skip).limit(limit)
        return list(self.db.execute(stmt).scalars().all())
        
    def delete(self, user: User) -> None:
        """Удалить пользователя."""
        self.db.delete(user)
        self.db.commit()
