"""Сервис для работы со снами"""

import logging
from datetime import datetime, timedelta, timezone
from uuid import UUID
import pytz

from sqlalchemy import select, func, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from models import Dream, User
from schemas import DreamCreate, DreamUpdate
from config import settings
from services.embedding_service import (
    cosine_similarity,
    deserialize_embedding,
    recalculate_dream_embedding,
    request_embedding,
)
from services.map_service import invalidate_user_map_cache
from services.rag_service import rebuild_dream_memory

logger = logging.getLogger(__name__)


async def get_user_timezone(user: User) -> pytz.timezone:
    """
    Получить timezone пользователя
    
    Args:
        user: Пользователь
    
    Returns:
        pytz timezone
    """
    try:
        return pytz.timezone(user.timezone)
    except:
        logger.warning(f"Invalid timezone {user.timezone} for user {user.id}, using UTC")
        return pytz.UTC


async def count_dreams_today(db: AsyncSession, user: User) -> int:
    """
    Подсчитать количество снов пользователя за сегодня
    
    Args:
        db: Сессия базы данных
        user: Пользователь
    
    Returns:
        Количество снов за сегодня
    """
    # Получаем timezone пользователя
    user_tz = await get_user_timezone(user)
    
    # Текущее время в timezone пользователя
    now = datetime.now(user_tz)
    
    # Начало дня (00:00) в timezone пользователя
    start_of_day = now.replace(hour=0, minute=0, second=0, microsecond=0)
    
    # Конец дня (23:59:59) в timezone пользователя
    end_of_day = start_of_day + timedelta(days=1) - timedelta(microseconds=1)
    
    # Конвертируем в UTC для запроса к БД
    start_of_day_utc = start_of_day.astimezone(pytz.UTC)
    end_of_day_utc = end_of_day.astimezone(pytz.UTC)
    
    result = await db.execute(
        select(func.count(Dream.id)).where(
            and_(
                Dream.user_id == user.id,
                Dream.recorded_at >= start_of_day_utc,
                Dream.recorded_at <= end_of_day_utc
            )
        )
    )
    
    count = result.scalar_one()
    logger.info(f"User {user.id} has {count} dreams today")
    return count


async def check_dreams_limit(db: AsyncSession, user: User) -> bool:
    """
    Проверить, не превышен ли лимит снов за день
    
    Args:
        db: Сессия базы данных
        user: Пользователь
    
    Returns:
        True если лимит не превышен
    """
    dreams_today = await count_dreams_today(db, user)
    limit = settings.dreams_per_day_limit
    
    return dreams_today < limit


async def create_dream(
    db: AsyncSession,
    user: User,
    dream_data: DreamCreate
) -> Dream:
    """
    Создать новый сон
    
    Args:
        db: Сессия базы данных
        user: Пользователь
        dream_data: Данные сна
    
    Returns:
        Созданный сон
    
    Raises:
        ValueError: Если превышен лимит снов
    """
    # Проверяем лимит
    if not await check_dreams_limit(db, user):
        raise ValueError(f"Daily limit of {settings.dreams_per_day_limit} dreams exceeded")
    
    # Автоматически генерируем title если не указан
    title = dream_data.title
    if not title and dream_data.content:
        clean = " ".join(dream_data.content.split())
        title = clean[:64]
    
    dream = Dream(
        user_id=user.id,
        title=title,
        content=dream_data.content,
        emoji=dream_data.emoji,
        comment=dream_data.comment,
    )
    
    db.add(dream)
    await db.commit()
    await db.refresh(dream)
    await invalidate_user_map_cache(user.id)
    
    logger.info(f"Dream created: {dream.id} for user {user.id}")
    return dream


async def get_dream_by_id(
    db: AsyncSession,
    dream_id: UUID,
    user: User
) -> Dream | None:
    """
    Получить сон по ID
    
    Args:
        db: Сессия базы данных
        dream_id: ID сна
        user: Пользователь
    
    Returns:
        Сон или None
    """
    result = await db.execute(
        select(Dream)
        .options(selectinload(Dream.analysis))
        .where(
            and_(
                Dream.id == dream_id,
                Dream.user_id == user.id
            )
        )
    )
    return result.scalar_one_or_none()


async def get_dreams_list(
    db: AsyncSession,
    user: User,
    page: int = 1,
    page_size: int = 10,
    date: str | None = None,
) -> tuple[list[Dream], int]:
    """
    Получить список снов пользователя с пагинацией
    
    Args:
        db: Сессия базы данных
        user: Пользователь
        page: Номер страницы (начиная с 1)
        page_size: Размер страницы
    
    Returns:
        Кортеж (список снов, общее количество)
    """
    # Подсчитываем общее количество
    filters = [Dream.user_id == user.id]

    if date:
        user_tz = await get_user_timezone(user)
        try:
            date_obj = datetime.strptime(date, "%Y-%m-%d").date()
            start_local = user_tz.localize(datetime.combine(date_obj, datetime.min.time()))
            end_local = user_tz.localize(datetime.combine(date_obj, datetime.max.time()))
            start_utc = start_local.astimezone(pytz.UTC)
            end_utc = end_local.astimezone(pytz.UTC)
            filters.append(Dream.recorded_at >= start_utc)
            filters.append(Dream.recorded_at <= end_utc)
        except ValueError:
            pass

    count_result = await db.execute(
        select(func.count(Dream.id)).where(and_(*filters))
    )
    total = count_result.scalar_one()
    
    # Получаем сны с пагинацией
    offset = (page - 1) * page_size
    result = await db.execute(
        select(Dream)
        .options(selectinload(Dream.analysis))
        .where(and_(*filters))
        .order_by(Dream.recorded_at.desc())
        .offset(offset)
        .limit(page_size)
    )
    dreams = result.scalars().all()
    
    return list(dreams), total


def _normalize_created_at(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


async def update_dream(
    db: AsyncSession,
    dream: Dream,
    dream_data: DreamUpdate
) -> Dream:
    """
    Обновить сон
    
    Args:
        db: Сессия базы данных
        dream: Сон для обновления
        dream_data: Новые данные
    
    Returns:
        Обновлённый сон
    """
    update_data = dream_data.model_dump(exclude_unset=True)
    
    if "created_at" in update_data and update_data["created_at"] is not None:
        normalized = _normalize_created_at(update_data["created_at"])
        now_utc = datetime.now(timezone.utc)
        if normalized > now_utc:
            raise ValueError("created_at_cannot_be_in_future")
        update_data["created_at"] = normalized
        update_data["recorded_at"] = normalized

    for field, value in update_data.items():
        setattr(dream, field, value)
    if {"title", "content", "comment"} & set(update_data.keys()):
        await recalculate_dream_embedding(db, dream)
        await rebuild_dream_memory(db, dream, dream.user_id)
    
    await db.commit()
    await db.refresh(dream)
    await invalidate_user_map_cache(dream.user_id)
    
    logger.info(f"Dream updated: {dream.id}")
    return dream


async def delete_dream(
    db: AsyncSession,
    dream: Dream
):
    """
    Удалить сон
    
    Args:
        db: Сессия базы данных
        dream: Сон для удаления
    """
    await db.delete(dream)
    await db.commit()
    await invalidate_user_map_cache(dream.user_id)
    logger.info(f"Dream deleted: {dream.id}")


async def search_dreams(
    db: AsyncSession,
    user: User,
    query: str
) -> list[tuple[Dream, float]]:
    """
    Поиск снов по тексту (PostgreSQL full-text search)
    
    Args:
        db: Сессия базы данных
        user: Пользователь
        query: Поисковый запрос
    
    Returns:
        Список найденных снов
    """
    # Простой поиск по содержимому (ILIKE)
    # В будущем можно улучшить с помощью PostgreSQL full-text search
    result = await db.execute(
        select(Dream)
        .options(selectinload(Dream.analysis))
        .where(
            and_(
                Dream.user_id == user.id,
                or_(
                    Dream.content.ilike(f"%{query}%"),
                    Dream.title.ilike(f"%{query}%"),
                    Dream.comment.ilike(f"%{query}%")
                )
            )
        )
        .order_by(Dream.recorded_at.desc())
    )
    dreams = list(result.scalars().all())
    scored: list[tuple[Dream, float]] = []
    q = query.lower().strip()
    for dream in dreams:
        score = 0.1
        if dream.title and q in dream.title.lower():
            score += 0.5
        if q in dream.content.lower():
            score += 0.4
        if dream.comment and q in dream.comment.lower():
            score += 0.1
        scored.append((dream, min(score, 1.0)))

    logger.info(f"Search '{query}' returned {len(scored)} results for user {user.id}")
    return scored


async def search_dreams_semantic(
    db: AsyncSession,
    user: User,
    query: str,
    limit: int = 50,
) -> list[tuple[Dream, float]]:
    query_vec = await request_embedding(query)
    result = await db.execute(
        select(Dream)
        .options(selectinload(Dream.analysis))
        .where(Dream.user_id == user.id)
        .order_by(Dream.recorded_at.desc())
        .limit(max(limit * 4, 100))
    )
    dreams = list(result.scalars().all())
    scored: list[tuple[Dream, float]] = []
    for dream in dreams:
        emb = deserialize_embedding(dream.embedding_text)
        if emb is None:
            # Lazy backfill so old rows become searchable.
            await recalculate_dream_embedding(db, dream)
            emb = deserialize_embedding(dream.embedding_text)
        if emb is None:
            continue
        score = cosine_similarity(query_vec, emb)
        if score > 0:
            scored.append((dream, score))
    await db.commit()
    scored.sort(key=lambda item: item[1], reverse=True)
    return scored[:limit]
