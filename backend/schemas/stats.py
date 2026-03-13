"""Pydantic схемы для статистики"""

from pydantic import BaseModel


class DayCount(BaseModel):
    date: str
    count: int


class ArchetypeStat(BaseModel):
    name: str
    count: int


class StatsResponse(BaseModel):
    total_dreams: int
    streak_days: int
    dreams_by_weekday: dict[str, int]
    dreams_last_14_days: list[DayCount] = []
    archetypes_top: list[ArchetypeStat] = []
    avg_time_of_day: str | None = None
