"""API эндпоинты для анализа снов"""

import logging
from uuid import UUID

from fastapi import APIRouter, HTTPException, status

from dependencies import DatabaseSession, VerifiedUser
from schemas import (
    AnalysisCreate,
    AnalysisResponse,
    AnalysisTaskResponse,
    AnalysisTaskStatusResponse,
    AnalysisListResponse,
)
from services.analysis_service import (
    create_analysis,
    get_analysis_by_dream_id,
    get_analysis_by_id,
    get_task_status,
    get_user_analyses,
)
from services.dream_service import get_dream_by_id

router = APIRouter(prefix="/analyses", tags=["Analyses"])
logger = logging.getLogger(__name__)


@router.post("", response_model=AnalysisTaskResponse, status_code=status.HTTP_202_ACCEPTED)
async def create_analysis_endpoint(
    analysis_data: AnalysisCreate,
    current_user: VerifiedUser,
    db: DatabaseSession
):
    """
    Запросить анализ сна
    
    - Создаёт фоновую задачу для анализа
    - Один сон может иметь только один анализ
    - Возвращает task_id для проверки статуса
    """
    # Получаем сон
    dream = await get_dream_by_id(db, analysis_data.dream_id, current_user)
    
    if not dream:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dream not found"
        )
    
    # Проверяем, что анализ не существует
    existing_analysis = await get_analysis_by_dream_id(db, dream.id, current_user)
    if existing_analysis:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Analysis for this dream already exists"
        )
    
    try:
        # Создаём анализ и запускаем задачу
        analysis, task_id = await create_analysis(db, dream, current_user)
        
        return {
            "analysis_id": analysis.id,
            "task_id": task_id,
            "status": analysis.status,
            "message": "Analysis task created. Use task_id to check status."
        }
    
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Failed to create analysis: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create analysis"
        )


@router.get("/task/{task_id}", response_model=AnalysisTaskStatusResponse)
async def get_task_status_endpoint(
    task_id: str,
    current_user: VerifiedUser
):
    """
    Получить статус задачи анализа по task_id
    
    - Возвращает статус: PENDING, PROCESSING, SUCCESS, FAILURE
    - Если SUCCESS, возвращает результат
    """
    try:
        status_dict = await get_task_status(task_id)
        
        return {
            "task_id": task_id,
            "status": status_dict["status"],
            "result": status_dict.get("result"),
            "error": status_dict.get("error"),
            "progress": status_dict.get("progress")
        }
    
    except Exception as e:
        logger.error(f"Failed to get task status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get task status"
        )


@router.get("/dream/{dream_id}", response_model=AnalysisResponse)
async def get_analysis_by_dream_endpoint(
    dream_id: UUID,
    current_user: VerifiedUser,
    db: DatabaseSession
):
    """
    Получить анализ сна по ID сна
    """
    analysis = await get_analysis_by_dream_id(db, dream_id, current_user)
    
    if not analysis:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Analysis not found for this dream"
        )
    
    return AnalysisResponse.model_validate(analysis)


@router.get("/{analysis_id}", response_model=AnalysisResponse)
async def get_analysis_endpoint(
    analysis_id: UUID,
    current_user: VerifiedUser,
    db: DatabaseSession
):
    """
    Получить анализ по ID
    """
    analysis = await get_analysis_by_id(db, analysis_id, current_user)
    
    if not analysis:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Analysis not found"
        )
    
    return AnalysisResponse.model_validate(analysis)


@router.get("", response_model=AnalysisListResponse)
async def get_analyses_endpoint(
    current_user: VerifiedUser,
    db: DatabaseSession
):
    """
    Получить список всех анализов пользователя
    
    - Сортировка по дате создания (новые сверху)
    - Максимум 100 анализов
    """
    try:
        analyses = await get_user_analyses(db, current_user, limit=100)
        
        return {
            "analyses": [AnalysisResponse.model_validate(a) for a in analyses],
            "total": len(analyses)
        }
    
    except Exception as e:
        logger.error(f"Failed to get analyses: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get analyses"
        )

