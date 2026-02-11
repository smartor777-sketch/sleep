"""Celery задачи для фоновой обработки"""

import logging
import asyncio
from datetime import datetime
from uuid import UUID

from celery_app import celery_app
from database import AsyncSessionLocal
from models import Analysis, Dream, User, AnalysisStatus, MessageRole
from llm_client import llm_client
from sqlalchemy import select

logger = logging.getLogger(__name__)


@celery_app.task(bind=True, name="tasks.analyze_dream")
def analyze_dream_task(self, analysis_id: str):
    """
    Фоновая задача для анализа сна

    Args:
        self: Celery task instance
        analysis_id: UUID анализа
    """
    # Запускаем асинхронную функцию в event loop
    return asyncio.run(_analyze_dream_async(self, analysis_id))


async def _analyze_dream_async(task_instance, analysis_id: str):
    """
    Асинхронная функция для анализа сна.
    Создаёт user-сообщение, собирает контекст, вызывает LLM, сохраняет assistant-сообщение.
    """
    from services.message_service import create_message, build_llm_context

    async with AsyncSessionLocal() as db:
        try:
            # Получаем анализ
            result = await db.execute(
                select(Analysis).where(Analysis.id == UUID(analysis_id))
            )
            analysis = result.scalar_one_or_none()

            if not analysis:
                logger.error(f"Analysis {analysis_id} not found")
                return None

            # Обновляем статус на "processing"
            analysis.status = AnalysisStatus.PROCESSING.value
            await db.commit()

            # Получаем сон
            result = await db.execute(
                select(Dream).where(Dream.id == analysis.dream_id)
            )
            dream = result.scalar_one_or_none()

            if not dream:
                logger.error(f"Dream {analysis.dream_id} not found")
                analysis.status = AnalysisStatus.FAILED.value
                analysis.error_message = "Dream not found"
                await db.commit()
                return None

            # Получаем пользователя для настроек
            result = await db.execute(
                select(User).where(User.id == analysis.user_id)
            )
            user = result.scalar_one_or_none()

            if not user:
                logger.error(f"User {analysis.user_id} not found")
                analysis.status = AnalysisStatus.FAILED.value
                analysis.error_message = "User not found"
                await db.commit()
                return None

            logger.info(f"Starting analysis {analysis_id} for dream {dream.id}")

            # Создаём user-сообщение (текст сна) в analysis_messages
            await create_message(
                db,
                user_id=user.id,
                dream_id=dream.id,
                role=MessageRole.USER.value,
                content=dream.content,
            )

            # Собираем контекст для LLM
            from prompts import get_chat_system_prompt
            system_prompt = get_chat_system_prompt(user.self_description)

            llm_messages = await build_llm_context(
                db,
                user_id=user.id,
                current_dream_id=dream.id,
                system_prompt=system_prompt,
            )

            # Отправляем запрос в LLM Service
            try:
                result_text = await llm_client.chat_completion(messages=llm_messages)

                # Сохраняем assistant-сообщение в analysis_messages
                await create_message(
                    db,
                    user_id=user.id,
                    dream_id=dream.id,
                    role=MessageRole.ASSISTANT.value,
                    content=result_text,
                )

                # Backward compat: записываем результат в Analysis.result
                analysis.result = result_text
                analysis.status = AnalysisStatus.COMPLETED.value
                analysis.completed_at = datetime.utcnow()

                await db.commit()

                logger.info(f"Analysis {analysis_id} completed successfully")
                return result_text

            except Exception as e:
                logger.error(f"LLM Service error for analysis {analysis_id}: {e}")
                analysis.status = AnalysisStatus.FAILED.value
                analysis.error_message = f"LLM Service error: {str(e)}"
                await db.commit()
                raise

        except Exception as e:
            logger.error(f"Failed to analyze dream {analysis_id}: {e}")

            # Обновляем статус на failed
            try:
                result = await db.execute(
                    select(Analysis).where(Analysis.id == UUID(analysis_id))
                )
                analysis = result.scalar_one_or_none()

                if analysis:
                    analysis.status = AnalysisStatus.FAILED.value
                    analysis.error_message = str(e)
                    await db.commit()
            except:
                pass

            raise


@celery_app.task(bind=True, name="tasks.reply_to_dream_chat")
def reply_to_dream_chat_task(self, user_id: str, dream_id: str):
    """
    Фоновая задача для ответа на follow-up сообщение в чате по сну.

    User-сообщение уже сохранено в analysis_messages (в API-хэндлере).
    Эта задача собирает контекст, вызывает LLM, сохраняет assistant-сообщение.
    """
    return asyncio.run(_reply_to_dream_chat_async(self, user_id, dream_id))


async def _reply_to_dream_chat_async(task_instance, user_id: str, dream_id: str):
    """Асинхронная реализация ответа на follow-up."""
    from services.message_service import create_message, build_llm_context

    async with AsyncSessionLocal() as db:
        try:
            # Получаем пользователя
            result = await db.execute(
                select(User).where(User.id == UUID(user_id))
            )
            user = result.scalar_one_or_none()
            if not user:
                logger.error(f"User {user_id} not found for chat reply")
                return None

            # Собираем контекст
            from prompts import get_chat_system_prompt
            system_prompt = get_chat_system_prompt(user.self_description)

            llm_messages = await build_llm_context(
                db,
                user_id=UUID(user_id),
                current_dream_id=UUID(dream_id),
                system_prompt=system_prompt,
            )

            # Вызываем LLM
            result_text = await llm_client.chat_completion(messages=llm_messages)

            # Сохраняем assistant-сообщение
            await create_message(
                db,
                user_id=UUID(user_id),
                dream_id=UUID(dream_id),
                role=MessageRole.ASSISTANT.value,
                content=result_text,
            )

            logger.info(f"Chat reply saved for dream {dream_id}")
            return result_text

        except Exception as e:
            logger.error(f"Failed to reply in dream chat {dream_id}: {e}")
            raise


@celery_app.task(name="tasks.send_email_task")
def send_email_task(to: str, subject: str, body: str):
    """
    Фоновая задача для отправки email

    Args:
        to: Email получателя
        subject: Тема письма
        body: Содержимое письма
    """
    from services.email_service import email_service

    try:
        email_service._send_email(to, subject, body, html=True)
        logger.info(f"Email sent to {to}")
    except Exception as e:
        logger.error(f"Failed to send email to {to}: {e}")
        raise
