"""Service for message task status."""

from celery.result import AsyncResult

from celery_app import celery_app


def get_message_task_status(task_id: str) -> dict:
    task_result = AsyncResult(task_id, app=celery_app)

    status_dict = {
        "task_id": task_id,
        "status": task_result.status,
        "result": None,
        "error": None,
    }

    if task_result.ready():
        if task_result.successful():
            status_dict["result"] = task_result.result
        elif task_result.failed():
            status_dict["error"] = str(task_result.info)

    return status_dict
