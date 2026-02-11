"""Сервис для работы с сообщениями анализа и сборки контекста для LLM"""

import logging
from uuid import UUID

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from models import AnalysisMessage, MessageRole, Dream, User

logger = logging.getLogger(__name__)

# Бюджет символов для контекста LLM (~7000 токенов)
CONTEXT_CHAR_BUDGET = 28000
# Максимум последних follow-up сообщений текущего сна
MAX_RECENT_MESSAGES = 20


async def create_message(
    db: AsyncSession,
    user_id: UUID,
    dream_id: UUID | None,
    role: str,
    content: str,
) -> AnalysisMessage:
    """Создать сообщение в чате анализа"""
    msg = AnalysisMessage(
        user_id=user_id,
        dream_id=dream_id,
        role=role,
        content=content,
    )
    db.add(msg)
    await db.commit()
    await db.refresh(msg)
    return msg


async def get_messages_for_dream(
    db: AsyncSession,
    user_id: UUID,
    dream_id: UUID,
    limit: int = 50,
    offset: int = 0,
) -> tuple[list[AnalysisMessage], int]:
    """Получить сообщения по сну для UI (с пагинацией)"""
    # Общее количество
    count_q = select(func.count(AnalysisMessage.id)).where(
        AnalysisMessage.user_id == user_id,
        AnalysisMessage.dream_id == dream_id,
    )
    total = (await db.execute(count_q)).scalar() or 0

    # Сами сообщения
    q = (
        select(AnalysisMessage)
        .where(
            AnalysisMessage.user_id == user_id,
            AnalysisMessage.dream_id == dream_id,
        )
        .order_by(AnalysisMessage.created_at.asc())
        .offset(offset)
        .limit(limit)
    )
    result = await db.execute(q)
    messages = list(result.scalars().all())
    return messages, total


async def build_llm_context(
    db: AsyncSession,
    user_id: UUID,
    current_dream_id: UUID,
    system_prompt: str,
) -> list[dict]:
    """
    Собрать полный контекст для LLM.

    Структура:
    1. system — системный промпт
    2. Якорные сообщения: для КАЖДОГО сна — первое user-сообщение (текст сна)
       + первый assistant-ответ (анализ), с префиксом [Сон: дата]
    3. Последние N сообщений follow-up диалога по текущему сну
    4. Если бюджет превышен — обрезаем старые не-якорные сообщения
    """
    messages: list[dict] = [{"role": "system", "text": system_prompt}]

    # --- Якорные сообщения: все сны пользователя ---
    dreams_q = (
        select(Dream)
        .where(Dream.user_id == user_id)
        .order_by(Dream.created_at.asc())
    )
    dreams_result = await db.execute(dreams_q)
    all_dreams = list(dreams_result.scalars().all())

    anchor_messages: list[dict] = []
    for dream in all_dreams:
        # Первое user-сообщение по этому сну
        first_user_q = (
            select(AnalysisMessage)
            .where(
                AnalysisMessage.user_id == user_id,
                AnalysisMessage.dream_id == dream.id,
                AnalysisMessage.role == MessageRole.USER.value,
            )
            .order_by(AnalysisMessage.created_at.asc())
            .limit(1)
        )
        first_user = (await db.execute(first_user_q)).scalar_one_or_none()

        # Первое assistant-сообщение
        first_asst_q = (
            select(AnalysisMessage)
            .where(
                AnalysisMessage.user_id == user_id,
                AnalysisMessage.dream_id == dream.id,
                AnalysisMessage.role == MessageRole.ASSISTANT.value,
            )
            .order_by(AnalysisMessage.created_at.asc())
            .limit(1)
        )
        first_asst = (await db.execute(first_asst_q)).scalar_one_or_none()

        date_str = dream.created_at.strftime("%d.%m.%Y")
        is_current = dream.id == current_dream_id

        if first_user:
            prefix = f"[Сон от {date_str}]" if not is_current else f"[Текущий сон от {date_str}]"
            anchor_messages.append({
                "role": "user",
                "text": f"{prefix}\n{first_user.content}",
            })
        if first_asst:
            anchor_messages.append({
                "role": "assistant",
                "text": first_asst.content,
            })

    # --- Follow-up сообщения текущего сна (кроме первого user + первого assistant) ---
    all_current_q = (
        select(AnalysisMessage)
        .where(
            AnalysisMessage.user_id == user_id,
            AnalysisMessage.dream_id == current_dream_id,
        )
        .order_by(AnalysisMessage.created_at.asc())
    )
    all_current = list((await db.execute(all_current_q)).scalars().all())

    # Пропускаем первое user + первое assistant (они уже в якорях)
    skip_user = True
    skip_asst = True
    follow_up: list[dict] = []
    for msg in all_current:
        if skip_user and msg.role == MessageRole.USER.value:
            skip_user = False
            continue
        if skip_asst and msg.role == MessageRole.ASSISTANT.value:
            skip_asst = False
            continue
        follow_up.append({"role": msg.role, "text": msg.content})

    # Обрезаем follow-up до последних N
    if len(follow_up) > MAX_RECENT_MESSAGES:
        follow_up = follow_up[-MAX_RECENT_MESSAGES:]

    # --- Сборка с учётом бюджета ---
    # system prompt не обрезаем
    system_chars = len(system_prompt)
    budget_remaining = CONTEXT_CHAR_BUDGET - system_chars

    # follow-up имеют приоритет — считаем их размер
    follow_up_chars = sum(len(m["text"]) for m in follow_up)
    budget_for_anchors = budget_remaining - follow_up_chars

    # Если якоря не влезают — обрезаем самые старые (но сохраняем текущий сон)
    trimmed_anchors: list[dict] = []
    used_chars = 0
    # Проходим с конца (новые сны приоритетнее)
    for msg in reversed(anchor_messages):
        msg_chars = len(msg["text"])
        if used_chars + msg_chars <= budget_for_anchors:
            trimmed_anchors.insert(0, msg)
            used_chars += msg_chars
        else:
            # Если не влезает — пропускаем старые
            continue

    messages.extend(trimmed_anchors)
    messages.extend(follow_up)

    return messages
