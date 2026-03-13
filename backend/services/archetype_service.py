"""Utilities for applying archetype deltas."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models import UserArchetype


async def apply_archetypes_delta(
    db: AsyncSession,
    user_id,
    delta: dict[str, int] | None,
) -> None:
    """Upsert archetype counters for a user."""
    if not delta:
        return
    for name, raw_value in delta.items():
        key = (name or "").strip()
        if not key:
            continue
        value = int(raw_value or 0)
        if value <= 0:
            continue
        row = (
            await db.execute(
                select(UserArchetype).where(
                    UserArchetype.user_id == user_id,
                    UserArchetype.name == key,
                )
            )
        ).scalar_one_or_none()
        if row is None:
            db.add(UserArchetype(user_id=user_id, name=key, count=value))
        else:
            row.count += value
