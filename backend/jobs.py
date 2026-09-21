"""Модуль для постановки задач в arq и проверки статуса."""

import logging
from arq.connections import ArqRedis, RedisSettings
from arq.jobs import Job
import redis.asyncio as aioredis

from config import settings

logger = logging.getLogger(__name__)

_pool: ArqRedis | None = None


async def get_redis_pool() -> ArqRedis:
    """Лениво создаём и переиспользуем ArqRedis пул."""
    global _pool
    if _pool is None:
        redis_settings = RedisSettings.from_dsn(settings.redis_url)
        conn_pool = aioredis.ConnectionPool.from_url(
            settings.redis_url, decode_responses=True
        )
        _pool = ArqRedis(pool_or_conn=conn_pool)
    return _pool


async def close_redis_pool():
    global _pool
    if _pool is not None:
        await _pool.aclose()
        _pool = None


async def enqueue_analyze_dream(analysis_id: str) -> str:
    """Поставить задачу анализа сна в очередь. Возвращает job_id."""
    pool = await get_redis_pool()
    job = await pool.enqueue_job(
        "analyze_dream_task",
        analysis_id,
        _job_try=4,
    )
    logger.info("Enqueued analyze_dream job %s for analysis %s", job.job_id, analysis_id)
    return job.job_id


async def enqueue_reply_chat(user_id: str, dream_id: str) -> str:
    """Поставить задачу ответа на follow-up в очередь. Возвращает job_id."""
    pool = await get_redis_pool()
    job = await pool.enqueue_job(
        "reply_to_dream_chat_task",
        user_id,
        dream_id,
        _job_try=4,
    )
    logger.info("Enqueued reply_chat job %s for dream %s", job.job_id, dream_id)
    return job.job_id


async def enqueue_send_email(to: str, subject: str, body: str) -> str:
    """Поставить задачу отправки email в очередь."""
    pool = await get_redis_pool()
    job = await pool.enqueue_job(
        "send_email_task",
        to,
        subject,
        body,
    )
    logger.info("Enqueued email job %s to %s", job.job_id, to)
    return job.job_id


async def get_job_status(job_id: str) -> dict:
    """Получить статус задачи по job_id."""
    pool = await get_redis_pool()
    job = Job(job_id, pool)
    try:
        status = await job.status()
    except Exception:
        return {"task_id": job_id, "status": "UNKNOWN", "result": None, "error": None}

    result_dict = {
        "task_id": job_id,
        "status": status,
        "result": None,
        "error": None,
    }

    if status == "complete":
        try:
            result_dict["result"] = await job.result()
        except Exception:
            pass
    elif status == "failed":
        try:
            result_dict["error"] = str(await job.result())
        except Exception:
            pass

    return result_dict
