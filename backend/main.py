"""Backend приложение JungAI"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config import settings
from database import init_db, close_db
from api import auth
from api import dreams
from api import analyses

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
    logger.info("Starting JungAI Backend...")
    await init_db()
    logger.info("Database initialized")
    yield
    # Shutdown
    logger.info("Shutting down JungAI Backend...")
    await close_db()
    logger.info("Database connection closed")


# Создание приложения FastAPI
app = FastAPI(
    title="JungAI Backend API",
    description="Backend API для мобильного приложения JungAI - запись и анализ снов",
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

# Подключение роутеров
app.include_router(auth.router, prefix="/api/v1")
app.include_router(dreams.router, prefix="/api/v1")
app.include_router(analyses.router, prefix="/api/v1")

# TODO: Подключить остальные роутеры
# app.include_router(user.router, prefix="/api/v1")
# app.include_router(voice.router, prefix="/api/v1")
# app.include_router(export.router, prefix="/api/v1")
# app.include_router(admin.router, prefix="/api/v1")


@app.get("/")
async def root():
    """Корневой эндпоинт"""
    return {
        "service": "JungAI Backend API",
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


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        reload=True,
        log_level=settings.log_level.lower()
    )

