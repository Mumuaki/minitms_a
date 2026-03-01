"""
main_integration.py — точка входа для сервиса Integration Hub.
Роутеры: gps, email, financial, google_sheets, settings.
Порт: 8004
Нет прямого доступа к БД — все модули stateless, работают с внешними API.
"""

import os
import logging
import traceback

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from backend.src.infrastructure.api.v1.endpoints import (
    gps,
    email,
    financial,
    google_sheets,
    settings,
)

app = FastAPI(
    title="MiniTMS Integration Hub",
    description="GPS Dozor, SMTP, Google Sheets, финансы, настройки",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

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

app.include_router(gps.router, prefix=api_v1_prefix)
app.include_router(email.router, prefix=api_v1_prefix)
app.include_router(financial.router, prefix=api_v1_prefix)
app.include_router(google_sheets.router, prefix=api_v1_prefix)
app.include_router(settings.router, prefix=api_v1_prefix)


@app.get("/health", tags=["System"])
async def health_check():
    """Проверка работоспособности Integration Hub."""
    return {"status": "ok", "service": "integration-hub"}
