"""Сервис лимитов — проверка доступа к анализу по тарифу"""

from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from models.user import User

# Free: 2 analyses per week
FREE_ANALYSES_PER_WEEK = 2


async def check_analysis_allowed(db: AsyncSession, user: User) -> bool:
    """
    Return True if user can create a new analysis.
    Pro/trial users have unlimited access.
    Free users get FREE_ANALYSES_PER_WEEK per rolling 7-day window.
    """
    # Trial expired? Downgrade
    if user.sub_type == "trial" and user.trial_started_at:
        elapsed = (datetime.now(timezone.utc) - user.trial_started_at).days
        if elapsed >= 7:
            user.sub_type = "free"
            user.trial_started_at = None
            await db.commit()

    if user.sub_type in ("pro", "trial"):
        return True

    # Free tier — weekly counter
    now = datetime.now(timezone.utc)
    if user.analyses_week_reset_at is None or (now - user.analyses_week_reset_at).days >= 7:
        user.analyses_week_count = 0
        user.analyses_week_reset_at = now
        await db.commit()

    return user.analyses_week_count < FREE_ANALYSES_PER_WEEK


async def increment_analysis_count(db: AsyncSession, user: User) -> None:
    """Increment the weekly analysis counter after a successful analysis creation."""
    if user.sub_type == "free":
        user.analyses_week_count += 1
        await db.commit()
