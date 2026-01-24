"""
Domain Entity: User

Сущность пользователя системы MiniTMS.
Отвечает за хранение данных аутентификации и авторизации.
"""

import enum
from datetime import datetime
from typing import Optional

from sqlalchemy import String, Boolean, Integer, DateTime, Enum as SQLEnum
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy.sql import func


class Base(DeclarativeBase):
    """Базовый класс для всех ORM моделей."""
    pass


class UserRole(enum.Enum):
    """
    Роли пользователей в системе.
    
    Согласно спецификации FR-AUTH-002:
    - Administrator: Полный доступ (управление пользователями, настройки)
    - Director: Управленческий доступ (финансы, планы, настройки интеграций)
    - Dispatcher: Операционный доступ (грузы, флот, email, Google Sheets)
    - Guest: Только чтение (отчёты, статусы)
    """
    ADMINISTRATOR = "administrator"
    DIRECTOR = "director"
    DISPATCHER = "dispatcher"
    GUEST = "guest"


class User(Base):
    """
    Сущность пользователя.
    
    Поля:
    - id: Уникальный идентификатор
    - email: Email (уникальный, используется для входа)
    - username: Имя пользователя для отображения
    - password_hash: Хеш пароля (bcrypt)
    - role: Роль пользователя (RBAC)
    - language: Предпочитаемый язык интерфейса (RU/EN/SK/PL)
    - is_active: Активен ли аккаунт
    - failed_login_attempts: Счётчик неудачных попыток входа
    - locked_until: Время до которого аккаунт заблокирован
    - created_at: Дата создания
    - updated_at: Дата последнего обновления
    """
    
    __tablename__ = "users"
    
    # Primary key
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    
    # Authentication fields
    email: Mapped[str] = mapped_column(
        String(255), 
        unique=True, 
        nullable=False,
        index=True
    )
    username: Mapped[str] = mapped_column(String(100), nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    
    # Authorization
    # Authorization
    role: Mapped[UserRole] = mapped_column(
        SQLEnum(UserRole, native_enum=False, values_callable=lambda x: [e.value for e in x]),
        nullable=False,
        default=UserRole.GUEST
    )
    
    # Localization (FR-LOC-001: RU, EN, SK, PL)
    language: Mapped[str] = mapped_column(
        String(2), 
        nullable=False, 
        default="ru"
    )
    
    # Account status
    is_active: Mapped[bool] = mapped_column(
        Boolean, 
        nullable=False, 
        default=True
    )
    
    # Security: блокировка после 5 неудачных попыток (FR-AUTH-003)
    failed_login_attempts: Mapped[int] = mapped_column(
        Integer, 
        nullable=False, 
        default=0
    )
    locked_until: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), 
        nullable=True,
        default=None
    )
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now()
    )
    
    def __repr__(self) -> str:
        return f"<User(id={self.id}, email='{self.email}', role={self.role.value})>"
    
    def is_locked(self) -> bool:
        """Проверяет, заблокирован ли аккаунт."""
        if self.locked_until is None:
            return False
        return datetime.now(self.locked_until.tzinfo) < self.locked_until
    
    def increment_failed_attempts(self) -> None:
        """Увеличивает счётчик неудачных попыток входа."""
        self.failed_login_attempts += 1
    
    def reset_failed_attempts(self) -> None:
        """Сбрасывает счётчик неудачных попыток и снимает блокировку."""
        self.failed_login_attempts = 0
        self.locked_until = None
