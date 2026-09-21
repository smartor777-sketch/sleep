"""arq worker для InnerCore — фоновые задачи (замена Celery)."""

import logging
from datetime import datetime
from uuid import UUID

from arq import cron
from arq.connections import RedisSettings

from config import settings
from database import AsyncSessionLocal
from models import Analysis, Dream, User, AnalysisStatus, MessageRole, AnalysisMessage
from llm_client import llm_client, LLMTransientError
from sqlalchemy import select
from services.embedding_service import recalculate_dream_embedding
from services.map_service import invalidate_user_map_cache

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Helper: notifications (safe wrappers)
# ---------------------------------------------------------------------------

async def _notify_analysis_started_safe(db, analysis, dream):
    try:
        from services.notification_service import notify_analysis_started
        await notify_analysis_started(db, analysis, dream)
    except Exception as e:
        logger.warning("Failed to notify analysis start for %s: %s", analysis.id, e)


async def _notify_analysis_completed_safe(db, analysis, dream):
    try:
        from services.notification_service import notify_analysis_completed, maybe_alert_admin_queue
        await notify_analysis_completed(db, analysis, dream)
        await maybe_alert_admin_queue(db)
    except Exception as e:
        logger.warning("Failed to notify analysis completion for %s: %s", analysis.id, e)


async def _notify_analysis_failed_safe(db, analysis, dream, error=None):
    try:
        from services.notification_service import notify_analysis_failed, maybe_alert_admin_queue
        await notify_analysis_failed(db, analysis, dream, error)
        await maybe_alert_admin_queue(db)
    except Exception as e:
        logger.warning("Failed to notify analysis failure for %s: %s", analysis.id, e)


# ---------------------------------------------------------------------------
# Task: analyze_dream
# ---------------------------------------------------------------------------

async def analyze_dream_task(ctx, analysis_id: str):
    """
    Фоновая задача для анализа сна.
    arq automatically retries on unhandled exception if max_retries configured via job kwargs.
    """
    from services.message_service import create_message
    from services.archetype_service import apply_archetypes_delta
    from services.rag_service import build_retrieval_context, rebuild_dream_memory
    from services import user_memory_service

    async with AsyncSessionLocal() as db:
        try:
            result = await db.execute(
                select(Analysis).where(Analysis.id == UUID(analysis_id))
            )
            analysis = result.scalar_one_or_none()

            if not analysis:
                logger.error(f"Analysis {analysis_id} not found")
                return None

            analysis.status = AnalysisStatus.PROCESSING.value
            await db.commit()

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
            await _notify_analysis_started_safe(db, analysis, dream)

            existing_user_msg = (
                await db.execute(
                    select(AnalysisMessage).where(
                        AnalysisMessage.user_id == user.id,
                        AnalysisMessage.dream_id == dream.id,
                        AnalysisMessage.role == MessageRole.USER.value,
                        AnalysisMessage.content == dream.content,
                    )
                )
            ).scalar_one_or_none()
            if existing_user_msg is None:
                await create_message(
                    db,
                    user_id=user.id,
                    dream_id=dream.id,
                    role=MessageRole.USER.value,
                    content=dream.content,
                )

            memory_doc = await user_memory_service.get_or_create(db, user.id)
            user_memory_md = memory_doc.content_md or ""
            memory_version = memory_doc.version

            rag_block = None
            try:
                retrieval = await build_retrieval_context(
                    db,
                    user_id=user.id,
                    dream=dream,
                    archetypes_delta={},
                )
                rag_block = retrieval.to_prompt_block().strip() or None
            except Exception as rag_err:
                logger.warning("Failed to build RAG context for analysis %s: %s", analysis_id, rag_err)

            try:
                was_completed_before = analysis.completed_at is not None
                payload = await llm_client.analyze_dream_structured(
                    dream_text=dream.content,
                    user_description=user.self_description,
                    user_memory_md=user_memory_md,
                    rag_context=rag_block,
                )
                result_text = payload.analysis_text

                existing_asst_msg = (
                    await db.execute(
                        select(AnalysisMessage).where(
                            AnalysisMessage.user_id == user.id,
                            AnalysisMessage.dream_id == dream.id,
                            AnalysisMessage.role == MessageRole.ASSISTANT.value,
                            AnalysisMessage.content == result_text,
                        )
                    )
                ).scalar_one_or_none()
                if existing_asst_msg is None:
                    await create_message(
                        db,
                        user_id=user.id,
                        dream_id=dream.id,
                        role=MessageRole.ASSISTANT.value,
                        content=result_text,
                    )

                analysis.result = result_text
                analysis.status = AnalysisStatus.COMPLETED.value
                analysis.completed_at = datetime.utcnow()
                if payload.title:
                    dream.title = payload.title[:64]
                if payload.gradient:
                    dream.gradient_color_1 = payload.gradient.color1
                    dream.gradient_color_2 = payload.gradient.color2
                if not was_completed_before:
                    await apply_archetypes_delta(db, user.id, payload.archetypes_delta)

                await db.commit()
                logger.info("Analysis %s committed, starting background indexing", analysis_id)

                if payload.memory_update:
                    try:
                        update_dict = {
                            k: v.model_dump() for k, v in payload.memory_update.items()
                        }
                        updated_doc = await user_memory_service.apply_memory_update(
                            db, user.id, update_dict, memory_version,
                        )
                        if updated_doc is None:
                            fresh_doc = await user_memory_service.get_or_create(db, user.id)
                            await user_memory_service.apply_memory_update(
                                db, user.id, update_dict, fresh_doc.version,
                            )
                        await db.commit()
                        logger.info("user.md updated for user %s", user.id)
                    except Exception as mem_err:
                        logger.warning("Failed to update user.md for user %s: %s", user.id, mem_err)
                        await db.rollback()

                try:
                    await recalculate_dream_embedding(db, dream)
                    await rebuild_dream_memory(
                        db,
                        dream=dream,
                        user_id=user.id,
                        archetypes_delta=payload.archetypes_delta,
                        symbol_entities=[item.model_dump() for item in payload.symbol_entities],
                    )
                    await db.commit()
                    await invalidate_user_map_cache(user.id)
                except Exception as postprocess_error:
                    logger.warning(
                        "Post-analysis indexing failed for analysis %s: %s",
                        analysis_id,
                        postprocess_error,
                    )
                    await db.rollback()

                logger.info(f"Analysis {analysis_id} completed successfully")
                await _notify_analysis_completed_safe(db, analysis, dream)
                return result_text

            except LLMTransientError as e:
                logger.warning("Transient LLM error for analysis %s: %s", analysis_id, e)
                analysis.status = AnalysisStatus.PENDING.value
                analysis.error_message = str(e)
                await db.commit()
                raise  # arq will retry

            except Exception as e:
                logger.error(f"LLM Service error for analysis {analysis_id}: {e}")
                await db.rollback()
                analysis = (
                    await db.execute(select(Analysis).where(Analysis.id == UUID(analysis_id)))
                ).scalar_one_or_none()
                if analysis:
                    analysis.status = AnalysisStatus.FAILED.value
                    analysis.error_message = f"LLM Service error: {str(e)}"
                    await db.commit()
                await _notify_analysis_failed_safe(db, analysis, dream, f"LLM Service error: {str(e)}")
                raise

        except LLMTransientError:
            raise
        except Exception as e:
            logger.error(f"Failed to analyze dream {analysis_id}: {e}")
            try:
                await db.rollback()
                result = await db.execute(
                    select(Analysis).where(Analysis.id == UUID(analysis_id))
                )
                analysis = result.scalar_one_or_none()
                if analysis:
                    analysis.status = AnalysisStatus.FAILED.value
                    analysis.error_message = str(e)
                    await db.commit()
                    await _notify_analysis_failed_safe(db, analysis, dream, str(e))
            except Exception as cleanup_error:
                logger.error(
                    "Failed to mark analysis %s as FAILED after error: %s",
                    analysis_id, cleanup_error,
                )
            raise


# ---------------------------------------------------------------------------
# Task: reply_to_dream_chat
# ---------------------------------------------------------------------------

async def reply_to_dream_chat_task(ctx, user_id: str, dream_id: str):
    """Фоновая задача для ответа на follow-up сообщение в чате по сну."""
    from services.message_service import create_message, build_llm_context
    from services import user_memory_service

    async with AsyncSessionLocal() as db:
        try:
            result = await db.execute(
                select(User).where(User.id == UUID(user_id))
            )
            user = result.scalar_one_or_none()
            if not user:
                logger.error(f"User {user_id} not found for chat reply")
                return None

            memory_doc = await user_memory_service.get_or_create(db, UUID(user_id))
            user_memory_md = memory_doc.content_md or ""

            from prompts import get_chat_system_prompt
            system_prompt = get_chat_system_prompt(user.self_description, user_memory_md)

            llm_messages = await build_llm_context(
                db,
                user_id=UUID(user_id),
                current_dream_id=UUID(dream_id),
                system_prompt=system_prompt,
            )

            result_text = await llm_client.chat_completion(
                messages=llm_messages,
                user_memory_md=user_memory_md,
            )

            await create_message(
                db,
                user_id=UUID(user_id),
                dream_id=UUID(dream_id),
                role=MessageRole.ASSISTANT.value,
                content=result_text,
            )

            logger.info(f"Chat reply saved for dream {dream_id}")
            return result_text

        except LLMTransientError as e:
            logger.warning("Transient LLM error for chat reply (dream %s): %s", dream_id, e)
            raise
        except Exception as e:
            logger.error(f"Failed to reply in dream chat {dream_id}: {e}")
            raise


# ---------------------------------------------------------------------------
# Task: send_email
# ---------------------------------------------------------------------------

async def send_email_task(ctx, to: str, subject: str, body: str):
    """Фоновая задача для отправки email."""
    from services.email_service import email_service

    try:
        email_service._send_email(to, subject, body)
        logger.info(f"Email sent to {to}")
    except Exception as e:
        logger.error(f"Failed to send email to {to}: {e}")
        raise


# ---------------------------------------------------------------------------
# arq Worker Settings
# ---------------------------------------------------------------------------

class WorkerSettings:
    """Настройки arq worker."""
    functions = [analyze_dream_task, reply_to_dream_chat_task, send_email_task]
    redis_settings = RedisSettings.from_dsn(settings.redis_url)
    max_jobs = 3
    poll_delay = 0.5
    job_timeout = 660  # 11 min — same as celery hard limit
    max_tries = 4
    retry_delay = 10  # seconds between retries
