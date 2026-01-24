"""
Pydantic схемы для управления пользователями.
"""

from typing import Optional
from pydantic import BaseModel, EmailStr, Field

# Импортируем базовый ответ из auth_schema, чтобы использовать ту же структуру
from backend.src.infrastructure.api.v1.schemas.auth_schema import UserResponse

class UserCreate(BaseModel):
    """
    Схема для создания нового пользователя.
    """
    email: EmailStr = Field(..., description="Уникальный Email")
    username: str = Field(..., min_length=2, max_length=100, description="Имя пользователя")
    password: str = Field(..., min_length=6, description="Пароль")
    role: str = Field(default="guest", description="Роль (administrator, director, dispatcher, guest)")
    language: str = Field(default="ru", min_length=2, max_length=2, description="Язык (ru, en, sk, pl)")

class UserUpdate(BaseModel):
    """
    Схема для обновления данных пользователя.
    Все поля опциональны.
    """
    email: Optional[EmailStr] = Field(None, description="Новый Email")
    username: Optional[str] = Field(None, min_length=2, max_length=100)
    role: Optional[str] = Field(None, description="Новая роль")
    language: Optional[str] = Field(None, min_length=2, max_length=2)
    is_active: Optional[bool] = Field(None, description="Статус активности")
    password: Optional[str] = Field(None, min_length=6, description="Новый пароль (если нужно сменить)")
