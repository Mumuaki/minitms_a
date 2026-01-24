"""
Точка входа в приложение MiniTMS Backend.

Инициализирует FastAPI приложение, подключает middleware и роутеры.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from backend.src.infrastructure.api.v1.endpoints import auth, users

# Инициализация приложения
app = FastAPI(
    title="MiniTMS API",
    description="Backend API для системы управления перевозками MiniTMS",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    swagger_ui_init_oauth={
        "usePkceWithAuthorizationCodeGrant": True,
    }
)

# Настройка CORS
# TODO: В production заменить ["*"] на конкретные домены Frontend'а
origins = [
    "http://localhost",
    "http://localhost:5173",  # Vite default port
    "http://localhost:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Подключение роутеров API v1
api_v1_prefix = "/api/v1"

app.include_router(auth.router, prefix=api_v1_prefix)
app.include_router(users.router, prefix=api_v1_prefix)


@app.get("/health", tags=["System"])
async def health_check():
    """Проверка работоспособности сервиса."""
    return {"status": "ok", "service": "MiniTMS Backend"}


if __name__ == "__main__":
    # Для отладки при прямом запуске файла
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
