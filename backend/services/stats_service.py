"""Service for user statistics."""

from datetime import datetime, timedelta

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from models import Dream, User, UserArchetype
from services.dream_service import get_user_timezone


async def get_user_stats(db: AsyncSession, user: User) -> dict:
    tz = await get_user_timezone(user)

    # total dreams
    total_q = select(func.count(Dream.id)).where(Dream.user_id == user.id)
    total = (await db.execute(total_q)).scalar() or 0

    # dreams by weekday
    dreams_q = select(Dream.recorded_at).where(Dream.user_id == user.id)
    rows = (await db.execute(dreams_q)).scalars().all()

    weekday_map = {"Mon": 0, "Tue": 0, "Wed": 0, "Thu": 0, "Fri": 0, "Sat": 0, "Sun": 0}
    times = []
    dates = set()

    for dt in rows:
        local = dt.astimezone(tz)
        weekday = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"][local.weekday()]
        weekday_map[weekday] += 1
        times.append(local.time())
        dates.add(local.date())

    # avg time of day
    avg_time = None
    if times:
        seconds = [t.hour * 3600 + t.minute * 60 + t.second for t in times]
        avg = int(sum(seconds) / len(seconds))
        avg_time = f"{avg // 3600:02d}:{(avg % 3600) // 60:02d}"

    # streak
    streak = 0
    if dates:
        today = datetime.now(tz).date()
        day = today
        while day in dates:
            streak += 1
            day -= timedelta(days=1)

    # last 14 days chart
    today = datetime.now(tz).date()
    dreams_by_date = {}
    for dt in rows:
        local = dt.astimezone(tz).date()
        dreams_by_date[local] = dreams_by_date.get(local, 0) + 1
    last_14_days = []
    for i in range(13, -1, -1):
        day = today - timedelta(days=i)
        last_14_days.append({"date": day.isoformat(), "count": dreams_by_date.get(day, 0)})

    archetypes_q = (
        select(UserArchetype)
        .where(UserArchetype.user_id == user.id)
        .order_by(UserArchetype.count.desc(), UserArchetype.name.asc())
        .limit(10)
    )
    archetypes = list((await db.execute(archetypes_q)).scalars().all())

    return {
        "total_dreams": total,
        "streak_days": streak,
        "dreams_by_weekday": weekday_map,
        "dreams_last_14_days": last_14_days,
        "archetypes_top": [{"name": item.name, "count": item.count} for item in archetypes],
        "avg_time_of_day": avg_time,
    }
