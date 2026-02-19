"""Сервис для анализа снов"""

import logging
from datetime import datetime
from uuid import UUID

from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from models import Analysis, AnalysisMessage, Dream, User, AnalysisStatus
from celery_app import celery_app

logger = logging.getLogger(__name__)


async def get_analysis_by_dream_id(
    db: AsyncSession,
    dream_id: UUID,
    user: User
) -> Analysis | None:
    """
    Получить анализ по ID сна
    
    Args:
        db: Сессия базы данных
        dream_id: ID сна
        user: Пользователь
    
    Returns:
        Анализ или None
    """
    result = await db.execute(
        select(Analysis).where(
            Analysis.dream_id == dream_id,
            Analysis.user_id == user.id
        )
    )
    return result.scalar_one_or_none()


async def create_analysis(
    db: AsyncSession,
    dream: Dream,
    user: User
) -> tuple[Analysis, str]:
    """
    Создать анализ сна и запустить фоновую задачу
    
    Args:
        db: Сессия базы данных
        dream: Сон для анализа
        user: Пользователь
    
    Returns:
        Кортеж (анализ, task_id)
    
    Raises:
        ValueError: Если анализ уже существует
    """
    from tasks import analyze_dream_task

    existing_analysis = await get_analysis_by_dream_id(db, dream.id, user)

    if existing_analysis:
        # Сбрасываем существующий анализ и чистим старые сообщения
        await db.execute(
            delete(AnalysisMessage).where(
                AnalysisMessage.dream_id == dream.id,
                AnalysisMessage.user_id == user.id,
            )
        )
        existing_analysis.result = None
        existing_analysis.error_message = None
        existing_analysis.completed_at = None
        existing_analysis.status = AnalysisStatus.PENDING.value
        await db.commit()
        await db.refresh(existing_analysis)

        task = analyze_dream_task.delay(str(existing_analysis.id))
        existing_analysis.celery_task_id = task.id
        await db.commit()

        logger.info(f"Analysis {existing_analysis.id} reset and requeued with task_id {task.id}")
        return existing_analysis, task.id

    # Создаём новую запись анализа
    analysis = Analysis(
        dream_id=dream.id,
        user_id=user.id,
        status=AnalysisStatus.PENDING.value
    )

    db.add(analysis)
    await db.commit()
    await db.refresh(analysis)

    task = analyze_dream_task.delay(str(analysis.id))
    analysis.celery_task_id = task.id
    await db.commit()

    logger.info(f"Analysis {analysis.id} created with task_id {task.id}")
    return analysis, task.id


async def get_analysis_by_id(
    db: AsyncSession,
    analysis_id: UUID,
    user: User
) -> Analysis | None:
    """
    Получить анализ по ID
    
    Args:
        db: Сессия базы данных
        analysis_id: ID анализа
        user: Пользователь
    
    Returns:
        Анализ или None
    """
    result = await db.execute(
        select(Analysis).where(
            Analysis.id == analysis_id,
            Analysis.user_id == user.id
        )
    )
    return result.scalar_one_or_none()


async def get_task_status(task_id: str) -> dict:
    """
    Получить статус Celery задачи
    
    Args:
        task_id: ID задачи
    
    Returns:
        Словарь со статусом задачи
    """
    from celery.result import AsyncResult
    
    task_result = AsyncResult(task_id, app=celery_app)
    
    status_dict = {
        "task_id": task_id,
        "status": task_result.status,
        "result": None,
        "error": None,
        "progress": None
    }
    
    if task_result.ready():
        if task_result.successful():
            status_dict["result"] = task_result.result
        elif task_result.failed():
            status_dict["error"] = str(task_result.info)
    
    return status_dict


async def get_user_analyses(
    db: AsyncSession,
    user: User,
    limit: int = 10
) -> list[Analysis]:
    """
    Получить список анализов пользователя
    
    Args:
        db: Сессия базы данных
        user: Пользователь
        limit: Максимальное количество анализов
    
    Returns:
        Список анализов
    """
    result = await db.execute(
        select(Analysis)
        .where(Analysis.user_id == user.id)
        .order_by(Analysis.created_at.desc())
        .limit(limit)
    )
    return list(result.scalars().all())

