"""Celery задачи для фоновой обработки"""

import logging
import asyncio
from datetime import datetime
from uuid import UUID

from celery_app import celery_app
from database import AsyncSessionLocal
from models import Analysis, Dream, User, AnalysisStatus
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
    Асинхронная функция для анализа сна
    
    Args:
        task_instance: Celery task instance
        analysis_id: UUID анализа
    
    Returns:
        Результат анализа или None при ошибке
    """
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
            
            # Отправляем запрос в LLM Service
            try:
                result_text = await llm_client.analyze_dream(
                    dream_text=dream.content,
                    user_description=user.self_description
                )
                
                # Сохраняем результат
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

