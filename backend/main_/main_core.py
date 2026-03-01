"""
main_core.py — точка входа для сервиса Core API.
Роутеры: auth, users, fleet, vehicles.
Порт: 8001
"""

import os
import logging
import traceback

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from backend.src.infrastructure.api.v1.endpoints import (
    auth,
    users,
    fleet,
    vehicles,
)

app = FastAPI(
    title="MiniTMS Core API",
    description="Auth, пользователи, автопарк, транспортные средства",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

# CORS — разрешаем origins через переменную окружения
_cors = os.getenv("CORS_ORIGINS", "")
origins = ["http://localhost", "http://localhost:5173", "http://localhost:3000"]
if _cors:
    origins.extend(o.strip() for o in _cors.split(",") if o.strip())

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(Exception)
async def _exception_handler(request: Request, exc: Exception):
    logging.exception("Unhandled exception: %s", exc)
    traceback.print_exc()
    from fastapi.responses import JSONResponse
    return JSONResponse(status_code=500, content={"detail": str(exc)})


api_v1_prefix = "/api/v1"

app.include_router(auth.router, prefix=api_v1_prefix)
app.include_router(users.router, prefix=api_v1_prefix)
app.include_router(fleet.router, prefix=api_v1_prefix)
app.include_router(vehicles.router, prefix=api_v1_prefix)


@app.get("/health", tags=["System"])
async def health_check():
    """Проверка работоспособности Core API."""
    return {"status": "ok", "service": "core-api"}
