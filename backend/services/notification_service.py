"""Сервис уведомлений: пользовательские, административные и контроль очереди анализов."""

import logging
from datetime import datetime
from uuid import UUID

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from config import settings
from models import Analysis, AnalysisStatus, Notification, User

logger = logging.getLogger(__name__)

SCOPE_USER = "user"
SCOPE_ADMIN = "admin"

TYPE_ANALYSIS_STARTED = "analysis_started"
TYPE_ANALYSIS_COMPLETED = "analysis_completed"
TYPE_ANALYSIS_FAILED = "analysis_failed"
TYPE_QUEUE_ALERT = "queue_alert"

ADMIN_QUEUE_ALERT_KEY = "admin_queue_alert_active"

_QUEUE_STATUSES = (AnalysisStatus.PENDING.value, AnalysisStatus.PROCESSING.value)


# ---------------------------------------------------------------------------
# Базовые операции
# ---------------------------------------------------------------------------

async def create_notification(
    db: AsyncSession,
    *,
    user_id: UUID | None,
    scope: str,
    type_: str,
    title: str,
    body: str | None = None,
    data: dict | None = None,
) -> Notification:
    notification = Notification(
        user_id=user_id,
        scope=scope,
        type=type_,
        title=title,
        body=body,
        data=data,
    )
    db.add(notification)
    await db.commit()
    return notification


async def list_notifications(
    db: AsyncSession,
    *,
    scope: str,
    user_id: UUID | None = None,
    limit: int = 50,
    offset: int = 0,
) -> tuple[list[Notification], int, int]:
    scope_cond = Notification.scope == scope
    user_cond = Notification.user_id == user_id if user_id is not None else None

    total_q = select(func.count(Notification.id)).where(scope_cond)
    unread_q = select(func.count(Notification.id)).where(scope_cond, Notification.is_read.is_(False))
    base = select(Notification).where(scope_cond)

    if user_cond is not None:
        total_q = total_q.where(user_cond)
        unread_q = unread_q.where(user_cond)
        base = base.where(user_cond)

    total = (await db.execute(total_q)).scalar() or 0
    unread = (await db.execute(unread_q)).scalar() or 0

    items = list(
        (
            await db.execute(
                base.order_by(Notification.created_at.desc()).offset(offset).limit(limit)
            )
        )
        .scalars()
        .all()
    )
    return items, total, unread


async def mark_notification_read(db: AsyncSession, notification_id: UUID, *, scope: str, user_id: UUID | None = None) -> bool:
    stmt = update(Notification).where(Notification.id == notification_id, Notification.scope == scope)
    if user_id is not None:
        stmt = stmt.where(Notification.user_id == user_id)
    result = await db.execute(stmt.values(is_read=True))
    await db.commit()
    return (result.rowcount or 0) > 0


async def mark_all_notifications_read(db: AsyncSession, *, scope: str, user_id: UUID | None = None) -> int:
    stmt = update(Notification).where(Notification.scope == scope, Notification.is_read.is_(False))
    if user_id is not None:
        stmt = stmt.where(Notification.user_id == user_id)
    result = await db.execute(stmt.values(is_read=True))
    await db.commit()
    return result.rowcount or 0


# ---------------------------------------------------------------------------
# Размер и позиция в очереди анализов
# ---------------------------------------------------------------------------

async def get_analysis_queue_size(db: AsyncSession) -> int:
    """Число анализов в очереди (pending + processing)."""
    result = await db.execute(
        select(func.count(Analysis.id)).where(Analysis.status.in_(_QUEUE_STATUSES))
    )
    return result.scalar() or 0


async def get_queue_position(db: AsyncSession, analysis_id: UUID) -> int | None:
    """Позиция анализа в очереди (1-based). None, если анализ не в очереди."""
    result = await db.execute(select(Analysis).where(Analysis.id == analysis_id))
    analysis = result.scalar_one_or_none()
    if not analysis or analysis.status not in _QUEUE_STATUSES or analysis.created_at is None:
        return None

    ahead = await db.execute(
        select(func.count(Analysis.id)).where(
            Analysis.status.in_(_QUEUE_STATUSES),
            Analysis.created_at < analysis.created_at,
        )
    )
    return (ahead.scalar() or 0) + 1


# ---------------------------------------------------------------------------
# Уведомления о ходе анализа
# ---------------------------------------------------------------------------

async def notify_analysis_started(db: AsyncSession, analysis: Analysis, dream) -> None:
    title = "Анализ запущен"
    body = f"«{dream.title or _dream_preview(dream)}» — InnerCore разбирает сон."
    data = {
        "dream_id": str(dream.id),
        "analysis_id": str(analysis.id),
        "dream_title": dream.title or _dream_preview(dream),
        "queue_position": await get_queue_position(db, analysis.id),
    }
    await create_notification(
        db,
        user_id=analysis.user_id,
        scope=SCOPE_USER,
        type_=TYPE_ANALYSIS_STARTED,
        title=title,
        body=body,
        data=data,
    )


async def notify_analysis_completed(db: AsyncSession, analysis: Analysis, dream) -> None:
    title = "Анализ готов"
    body = f"Разбор сна «{dream.title or _dream_preview(dream)}» готов."
    data = {
        "dream_id": str(dream.id),
        "analysis_id": str(analysis.id),
        "dream_title": dream.title or _dream_preview(dream),
    }
    await create_notification(
        db,
        user_id=analysis.user_id,
        scope=SCOPE_USER,
        type_=TYPE_ANALYSIS_COMPLETED,
        title=title,
        body=body,
        data=data,
    )


async def notify_analysis_failed(db: AsyncSession, analysis: Analysis, dream, error: str | None = None) -> None:
    title = "Анализ не удался"
    body = f"Не получилось разобрать сон «{dream.title if dream else _dream_preview(dream)}»."
    data = {
        "dream_id": str(dream.id) if dream else None,
        "analysis_id": str(analysis.id),
        "dream_title": dream.title if dream else None,
        "error": error,
    }
    await create_notification(
        db,
        user_id=analysis.user_id,
        scope=SCOPE_USER,
        type_=TYPE_ANALYSIS_FAILED,
        title=title,
        body=body,
        data=data,
    )


def _dream_preview(dream) -> str:
    if dream is None:
        return "сон"
    text = getattr(dream, "content", None) or ""
    words = [w for w in text.split() if w]
    return " ".join(words[:5])


# ---------------------------------------------------------------------------
# Административный алерт: очередь >= N
# ---------------------------------------------------------------------------

async def maybe_alert_admin_queue(db: AsyncSession) -> None:
    """При достижении очередью порога уведомляем админа (панель + email) один раз.

    Флаг «admin_queue_alert_active» снимается, когда очередь падает ниже порога,
    поэтому каждый новый «залп» очереди даёт ровно одно уведомление.
    """
    queue_size = await get_analysis_queue_size(db)
    threshold = settings.analysis_queue_alert_threshold
    active = await _queue_alert_active(db)

    if queue_size >= threshold and not active:
        logger.warning("Analysis queue reached %s (threshold %s) — alerting admin", queue_size, threshold)
        try:
            from services import settings_service
            await settings_service.set_setting(db, ADMIN_QUEUE_ALERT_KEY, True)
        except Exception as set_err:  # pragma: no cover
            logger.warning("Failed to set queue alert flag: %s", set_err)
        try:
            await create_notification(
                db,
                user_id=None,
                scope=SCOPE_ADMIN,
                type_=TYPE_QUEUE_ALERT,
                title="Очередь анализов перегружена",
                body=f"В очереди {queue_size} анализов (порог {threshold}). "
                     "Проверьте состояние celery-воркеров (innercore-llm / celery-prod).",
                data={"queue_size": queue_size, "threshold": threshold},
            )
        except Exception as notif_err:  # pragma: no cover
            logger.warning("Failed to create admin queue alert notification: %s", notif_err)
        await _email_admins_queue_alert(db, queue_size)
    elif queue_size < threshold and active:
        try:
            from services import settings_service
            await settings_service.set_setting(db, ADMIN_QUEUE_ALERT_KEY, False)
        except Exception as reset_err:  # pragma: no cover
            logger.warning("Failed to reset queue alert flag: %s", reset_err)


async def _queue_alert_active(db: AsyncSession) -> bool:
    try:
        from services import settings_service
        return await settings_service.get_setting_bool(db, ADMIN_QUEUE_ALERT_KEY, default=False)
    except Exception:  # pragma: no cover
        return False


async def _email_admins_queue_alert(db: AsyncSession, queue_size: int) -> None:
    recipients = await _collect_admin_emails(db)
    if not recipients:
        logger.warning("No admin email configured — queue alert email skipped")
        return

    subject = "InnerCore: очередь анализов ≥ 10"
    body = (
        "<p>Очередь анализов снов превысила порог.</p>"
        f"<p>Текущий размер очереди: <b>{queue_size}</b>.</p>"
        "<p>Проверьте состояние celery-воркеров и LLM-сервиса.</p>"
    )
    for to in recipients:
        try:
            from tasks import send_email_task
            send_email_task.delay(to, subject, body)
        except Exception as e:
            logger.error("Failed to enqueue queue-alert email to %s: %s", to, e)


async def _collect_admin_emails(db: AsyncSession) -> set[str]:
    emails: set[str] = set()
    if settings.admin_email:
        emails.update(e.strip() for e in settings.admin_email.split(",") if e.strip())
    try:
        rows = (
            await db.execute(
                select(User.email).where(
                    User.is_admin.is_(True),
                    User.email.isnot(None),
                    User.email_verified.is_(True),
                )
            )
        ).all()
        emails.update(r[0] for r in rows if r[0])
    except Exception as err:  # pragma: no cover
        logger.warning("Failed to collect admin emails from DB: %s", err)
    return emails
