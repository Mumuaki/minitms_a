"""
main_scraping.py — точка входа для сервиса Scraping Worker.
Роутеры: scraping.
Порт: 8003
Требует: Playwright + Xvfb + noVNC (собирается из Dockerfile, не Dockerfile.service)
"""

import os
import logging
import traceback

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from backend.src.infrastructure.api.v1.endpoints import scraping

app = FastAPI(
    title="MiniTMS Scraping Worker",
    description="Скрапинг Trans.eu через Playwright + Chromium",
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


from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    from fastapi.responses import JSONResponse
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "type": "about:blank",
            "title": "HTTP Error",
            "status": exc.status_code,
            "detail": str(exc.detail),
            "instance": str(request.url.path)
        }
    )

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    from fastapi.responses import JSONResponse
    return JSONResponse(
        status_code=422,
        content={
            "type": "about:blank",
            "title": "Validation Error",
            "status": 422,
            "detail": str(exc.errors()),
            "instance": str(request.url.path)
        }
    )

@app.exception_handler(Exception)
async def _exception_handler(request: Request, exc: Exception):
    logging.exception("Unhandled exception: %s", exc)
    traceback.print_exc()
    from fastapi.responses import JSONResponse
    return JSONResponse(
        status_code=500, 
        content={
            "type": "about:blank",
            "title": "Internal Server Error",
            "status": 500,
            "detail": str(exc),
            "instance": str(request.url.path)
        }
    )


api_v1_prefix = "/api/v1"

app.include_router(scraping.router, prefix=api_v1_prefix)


@app.get("/health", tags=["System"])
async def health_check():
    """Проверка работоспособности Scraping Worker."""
    return {"status": "ok", "service": "scraping-worker"}
