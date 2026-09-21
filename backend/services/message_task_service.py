"""Service for message task status."""

from jobs import get_job_status


async def get_message_task_status(task_id: str) -> dict:
    return await get_job_status(task_id)
