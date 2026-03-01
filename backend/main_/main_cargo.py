"""
main_cargo.py — точка входа для сервиса Cargo Engine.
Роутеры: cargos, routes, route_planning.
Порт: 8002
"""

import os
import logging
import traceback

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from backend.src.infrastructure.api.v1.endpoints import (
    cargos,
    routes,
    route_planning,
)

app = FastAPI(
    title="MiniTMS Cargo Engine",
    description="Грузы, маршруты, планирование (OSRM, расчёт прибыльности)",
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

app.include_router(cargos.router, prefix=api_v1_prefix)
app.include_router(routes.router, prefix=api_v1_prefix)
app.include_router(route_planning.router, prefix=api_v1_prefix)


@app.get("/health", tags=["System"])
async def health_check():
    """Проверка работоспособности Cargo Engine."""
    return {"status": "ok", "service": "cargo-engine"}
