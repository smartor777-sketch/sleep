"""Celery приложение для фоновых задач"""

from celery import Celery
from config import settings

# Создание Celery приложения
celery_app = Celery(
    "jungai",
    broker=settings.redis_url,
    backend=settings.redis_url,
    include=["tasks"]  # Импортируем модуль с задачами
)

# Конфигурация Celery
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,  # 30 минут максимум на задачу
    task_soft_time_limit=25 * 60,  # 25 минут soft limit
)

