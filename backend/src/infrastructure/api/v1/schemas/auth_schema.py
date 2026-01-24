"""
Pydantic схемы для модуля авторизации.

Определяет структуры данных для:
- Запросов (Login, Refresh)
- Ответов (Token, User, Error)
"""

from typing import Optional
from pydantic import BaseModel, EmailStr, Field


class LoginRequest(BaseModel):
    """
    Схема запроса на вход в систему.
    
    Используется для POST /auth/login.
    """
    email: EmailStr = Field(..., description="Email пользователя")
    password: str = Field(..., min_length=6, description="Пароль")
    remember_me: bool = Field(default=False, description="Запомнить меня (30 дней)")


class RefreshRequest(BaseModel):
    """
    Схема запроса на обновление токена.
    
    Используется для POST /auth/refresh.
    """
    refresh_token: str = Field(..., description="Refresh token для обновления")


class TokenResponse(BaseModel):
    """
    Схема ответа с токенами.
    
    Возвращается при успешном логине или refresh.
    """
    access_token: str = Field(..., description="JWT Access Token")
    refresh_token: str = Field(..., description="JWT Refresh Token")
    token_type: str = Field(default="bearer", description="Тип токена")


class UserResponse(BaseModel):
    """
    Схема профиля пользователя.
    
    Возвращается для GET /auth/me.
    """
    id: int = Field(..., description="ID пользователя")
    email: str = Field(..., description="Email пользователя")
    username: str = Field(..., description="Имя пользователя")
    role: str = Field(..., description="Роль (administrator, director, dispatcher, observer)")
    language: str = Field(default="ru", description="Язык интерфейса")
    is_active: bool = Field(default=True, description="Активен ли аккаунт")


class ErrorResponse(BaseModel):
    """
    Стандартизированная схема ошибки (RFC 7807).
    
    Используется для всех ошибок API.
    """
    type: str = Field(default="about:blank", description="URI типа ошибки")
    title: str = Field(..., description="Краткое описание ошибки")
    status: int = Field(..., description="HTTP статус код")
    detail: str = Field(..., description="Детальное описание ошибки")
    instance: Optional[str] = Field(default=None, description="URI ресурса, вызвавшего ошибку")
