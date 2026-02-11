"""Pydantic схемы для статистики"""

from pydantic import BaseModel


class StatsResponse(BaseModel):
    total_dreams: int
    streak_days: int
    dreams_by_weekday: dict[str, int]
    avg_time_of_day: str | None = None
