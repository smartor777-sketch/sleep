"""API эндпоинты для статистики"""

from fastapi import APIRouter

from dependencies import CurrentUser, DatabaseSession
from services.stats_service import get_user_stats

router = APIRouter(prefix="/stats", tags=["Stats"])


from schemas.stats import StatsResponse


@router.get("/me", response_model=StatsResponse)
async def get_stats(current_user: CurrentUser, db: DatabaseSession):
    return await get_user_stats(db, current_user)
