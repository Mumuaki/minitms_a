"""
SQLAlchemy Database Configuration.

Настройка подключения к PostgreSQL и создание сессий.
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from typing import Generator

import os
from dotenv import load_dotenv

from backend.src.domain.entities.user import Base

# Загружаем .env если есть (в Docker переменные задаются через environment)
_env_path = os.path.join(os.path.dirname(__file__), "../../../../../backend/.env")
if os.path.exists(_env_path):
    load_dotenv(_env_path)
# В Docker: DATABASE_URL приходит из docker-compose environment
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/mini-tms")


# Engine — подключение к БД
engine = create_engine(
    DATABASE_URL,
    echo=False,  # True для отладки SQL запросов
    pool_pre_ping=True,  # Проверка соединения перед использованием
)


# SessionLocal — фабрика сессий
SessionLocal = sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
)


def get_db() -> Generator[Session, None, None]:
    """
    Dependency для получения сессии БД.
    
    Использование в FastAPI:
        @router.get("/users")
        def get_users(db: Session = Depends(get_db)):
            ...
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def create_tables() -> None:
    """
    Создаёт все таблицы в БД.
    
    Используется для разработки. В продакшене — Alembic миграции.
    """
    Base.metadata.create_all(bind=engine)
