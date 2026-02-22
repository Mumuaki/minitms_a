"""
Точка входа в приложение MiniTMS Backend.

Инициализирует FastAPI приложение, подключает middleware и роутеры.
"""

import logging
import traceback

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from backend.src.infrastructure.api.v1.endpoints import (
    auth,
    users,
    cargos,
    route_planning,
    fleet,
    vehicles,
    gps,
    email,
    financial,
    google_sheets,
    settings,
    scraping,
    routes,
)

# Инициализация приложения
# Main application entry point
# Forced reload for GPS schema update
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
import os
_cors = os.getenv("CORS_ORIGINS", "")
origins = [
    "http://localhost",
    "http://localhost:5173",
    "http://localhost:3000",
    "http://127.0.0.1:5173",
    "http://127.0.0.1:3000",
]
if _cors:
    origins.extend(o.strip() for o in _cors.split(",") if o.strip())

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# #region agent log
@app.exception_handler(Exception)
async def _agent_exception_handler(request: Request, exc: Exception):
    logging.exception("Unhandled exception: %s", exc)
    traceback.print_exc()
    from fastapi.responses import JSONResponse
    return JSONResponse(status_code=500, content={"detail": str(exc)})
# #endregion

# Подключение роутеров API v1
api_v1_prefix = "/api/v1"

app.include_router(auth.router, prefix=api_v1_prefix)
app.include_router(users.router, prefix=api_v1_prefix)
app.include_router(cargos.router, prefix=api_v1_prefix)
app.include_router(route_planning.router, prefix=api_v1_prefix)
app.include_router(fleet.router, prefix=api_v1_prefix)
app.include_router(vehicles.router, prefix=api_v1_prefix)
app.include_router(gps.router, prefix=api_v1_prefix)
app.include_router(email.router, prefix=api_v1_prefix)
app.include_router(financial.router, prefix=api_v1_prefix)
app.include_router(google_sheets.router, prefix=api_v1_prefix)
app.include_router(settings.router, prefix=api_v1_prefix)
app.include_router(scraping.router, prefix=api_v1_prefix)
app.include_router(routes.router, prefix=api_v1_prefix)


@app.get("/health", tags=["System"])
async def health_check():
    """Проверка работоспособности сервиса."""
    return {"status": "ok", "service": "MiniTMS Backend"}


if __name__ == "__main__":
    # Для отладки при прямом запуске файла
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
