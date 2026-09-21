"""Сервис для анализа снов"""

import logging
from datetime import datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models import Analysis, Dream, User, AnalysisStatus

logger = logging.getLogger(__name__)


async def get_analysis_by_dream_id(
    db: AsyncSession,
    dream_id: UUID,
    user: User
) -> Analysis | None:
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
    user: User,
    allow_retry: bool = False,
) -> tuple[Analysis, str]:
    from jobs import enqueue_analyze_dream

    existing_analysis = await get_analysis_by_dream_id(db, dream.id, user)

    if existing_analysis:
        if existing_analysis.status in {
            AnalysisStatus.PENDING.value,
            AnalysisStatus.PROCESSING.value,
        }:
            raise ValueError("analysis_already_exists")
        if existing_analysis.status == AnalysisStatus.COMPLETED.value:
            raise ValueError("analysis_already_exists")
        if existing_analysis.status == AnalysisStatus.FAILED.value and allow_retry:
            existing_analysis.status = AnalysisStatus.PENDING.value
            existing_analysis.error_message = None
            existing_analysis.completed_at = None
            analysis = existing_analysis
        else:
            raise ValueError("analysis_already_exists")
    else:
        analysis = Analysis(
            dream_id=dream.id,
            user_id=user.id,
            status=AnalysisStatus.PENDING.value
        )

    db.add(analysis)
    await db.commit()
    await db.refresh(analysis)

    job_id = await enqueue_analyze_dream(str(analysis.id))
    analysis.celery_task_id = job_id
    await db.commit()

    logger.info(f"Analysis {analysis.id} created with job_id {job_id}")

    try:
        from services.notification_service import maybe_alert_admin_queue
        await maybe_alert_admin_queue(db)
    except Exception as alert_err:
        logger.warning("Admin queue alert check failed: %s", alert_err)

    return analysis, job_id


async def get_analysis_by_id(
    db: AsyncSession,
    analysis_id: UUID,
    user: User
) -> Analysis | None:
    result = await db.execute(
        select(Analysis).where(
            Analysis.id == analysis_id,
            Analysis.user_id == user.id
        )
    )
    return result.scalar_one_or_none()


async def get_task_status(task_id: str) -> dict:
    from jobs import get_job_status
    return await get_job_status(task_id)


async def get_user_analyses(
    db: AsyncSession,
    user: User,
    limit: int = 10
) -> list[Analysis]:
    result = await db.execute(
        select(Analysis)
        .where(Analysis.user_id == user.id)
        .order_by(Analysis.created_at.desc())
        .limit(limit)
    )
    return list(result.scalars().all())
