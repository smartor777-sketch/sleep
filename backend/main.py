"""Backend приложение InnerCore"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

from config import settings
from database import init_db, close_db
from api import auth
from api import dreams
from api import analyses
from api import audio
from api import map
from api import messages
from api import users
from api import stats
from api import billing

# Настройка логирования
logging.basicConfig(
    level=getattr(logging, settings.log_level),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle manager для инициализации и закрытия ресурсов"""
    # Startup
    logger.info("Starting InnerCore Backend...")
    await init_db()
    logger.info("Database initialized")
    yield
    # Shutdown
    logger.info("Shutting down InnerCore Backend...")
    await close_db()
    logger.info("Database connection closed")


# Создание приложения FastAPI
app = FastAPI(
    title="InnerCore Backend API",
    description="Backend API для мобильного приложения InnerCore - запись и анализ снов",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Минимальная версия клиента
_EXEMPT_PATHS = {"/", "/health", "/api/v1/app/version"}


def _parse_version(v: str) -> tuple[int, ...]:
    parts = []
    for p in v.split("."):
        try:
            parts.append(int(p))
        except ValueError:
            break
    return tuple(parts)


class MinVersionMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if request.url.path in _EXEMPT_PATHS:
            return await call_next(request)

        client_version = request.headers.get("X-App-Version")
        if client_version is None:
            # Старые клиенты без заголовка — блокируем
            return JSONResponse(
                status_code=426,
                content={
                    "detail": "Обновите приложение / Please update the app",
                    "min_version": APP_MIN_VERSION,
                    "download_url": APP_DOWNLOAD_URL,
                },
            )

        if _parse_version(client_version) < _parse_version(APP_MIN_VERSION):
            return JSONResponse(
                status_code=426,
                content={
                    "detail": "Обновите приложение / Please update the app",
                    "min_version": APP_MIN_VERSION,
                    "download_url": APP_DOWNLOAD_URL,
                },
            )

        return await call_next(request)


app.add_middleware(MinVersionMiddleware)


# Подключение роутеров
app.include_router(auth.router, prefix="/api/v1")
app.include_router(dreams.router, prefix="/api/v1")
app.include_router(analyses.router, prefix="/api/v1")
app.include_router(audio.router, prefix="/api/v1")
app.include_router(map.router, prefix="/api/v1")
app.include_router(messages.router, prefix="/api/v1")
app.include_router(users.router, prefix="/api/v1")
app.include_router(stats.router, prefix="/api/v1")
app.include_router(billing.router, prefix="/api/v1")

# TODO: Подключить остальные роутеры
# app.include_router(user.router, prefix="/api/v1")
# app.include_router(voice.router, prefix="/api/v1")
# app.include_router(export.router, prefix="/api/v1")
# app.include_router(admin.router, prefix="/api/v1")


@app.get("/")
async def root():
    """Корневой эндпоинт"""
    return {
        "service": "InnerCore Backend API",
        "version": "1.0.0",
        "status": "running"
    }


@app.get("/health")
async def health_check():
    """Проверка здоровья сервиса"""
    return {
        "status": "ok",
        "service": "backend",
        "version": "1.0.0"
    }


APP_LATEST_VERSION = "0.4.0"
APP_MIN_VERSION = "0.3.2"
APP_DOWNLOAD_URL = "https://github.com/core-euler/sna_net/releases/latest/download/app-release.apk"


@app.get("/api/v1/app/version")
async def app_version():
    """Текущая версия мобильного приложения"""
    return {
        "version": APP_LATEST_VERSION,
        "download_url": APP_DOWNLOAD_URL,
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        reload=True,
        log_level=settings.log_level.lower()
    )
