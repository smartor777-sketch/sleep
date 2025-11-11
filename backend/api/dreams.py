"""API эндпоинты для управления снами"""

import logging
import math
from uuid import UUID

from fastapi import APIRouter, HTTPException, status, UploadFile, File, Query

from dependencies import DatabaseSession, VerifiedUser
from schemas import (
    DreamCreate,
    DreamUpdate,
    DreamResponse,
    DreamListResponse,
    DreamSearchResponse,
    MessageResponse,
)
from services.dream_service import (
    create_dream,
    get_dream_by_id,
    get_dreams_list,
    update_dream,
    delete_dream,
    search_dreams,
)
from services.storage_service import storage_service
from models import Analysis

router = APIRouter(prefix="/dreams", tags=["Dreams"])
logger = logging.getLogger(__name__)


@router.post("", response_model=DreamResponse, status_code=status.HTTP_201_CREATED)
async def create_dream_endpoint(
    dream_data: DreamCreate,
    current_user: VerifiedUser,
    db: DatabaseSession
):
    """
    Создать новый сон
    
    - Проверяет лимит снов за день (5 снов)
    - Создаёт сон с текущей датой и временем
    """
    try:
        dream = await create_dream(db, current_user, dream_data)
        
        # Добавляем информацию о наличии анализа
        response_data = DreamResponse.model_validate(dream)
        response_data.has_analysis = False  # Новый сон не имеет анализа
        
        return response_data
    
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Failed to create dream: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create dream"
        )


@router.get("", response_model=DreamListResponse)
async def get_dreams_endpoint(
    current_user: VerifiedUser,
    db: DatabaseSession,
    page: int = Query(1, ge=1, description="Номер страницы"),
    page_size: int = Query(10, ge=1, le=100, description="Размер страницы")
):
    """
    Получить список снов пользователя с пагинацией
    
    - Сортировка по дате создания (новые сверху)
    - Поддержка пагинации
    """
    try:
        dreams, total = await get_dreams_list(db, current_user, page, page_size)
        
        # Проверяем наличие анализов для снов
        dreams_with_analysis = []
        for dream in dreams:
            dream_response = DreamResponse.model_validate(dream)
            # Проверяем, есть ли анализ
            dream_response.has_analysis = dream.analysis is not None
            dreams_with_analysis.append(dream_response)
        
        total_pages = math.ceil(total / page_size) if total > 0 else 0
        
        return {
            "dreams": dreams_with_analysis,
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": total_pages
        }
    
    except Exception as e:
        logger.error(f"Failed to get dreams: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get dreams"
        )


@router.get("/search", response_model=DreamSearchResponse)
async def search_dreams_endpoint(
    current_user: VerifiedUser,
    db: DatabaseSession,
    q: str = Query(..., min_length=1, description="Поисковый запрос")
):
    """
    Поиск снов по тексту
    
    - Поиск по содержимому, заголовку и комментарию
    - Регистронезависимый поиск
    """
    try:
        dreams = await search_dreams(db, current_user, q)
        
        # Проверяем наличие анализов
        dreams_with_analysis = []
        for dream in dreams:
            dream_response = DreamResponse.model_validate(dream)
            dream_response.has_analysis = dream.analysis is not None
            dreams_with_analysis.append(dream_response)
        
        return {
            "dreams": dreams_with_analysis,
            "total": len(dreams_with_analysis),
            "query": q
        }
    
    except Exception as e:
        logger.error(f"Failed to search dreams: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to search dreams"
        )


@router.get("/{dream_id}", response_model=DreamResponse)
async def get_dream_endpoint(
    dream_id: UUID,
    current_user: VerifiedUser,
    db: DatabaseSession
):
    """
    Получить сон по ID
    """
    dream = await get_dream_by_id(db, dream_id, current_user)
    
    if not dream:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dream not found"
        )
    
    response_data = DreamResponse.model_validate(dream)
    response_data.has_analysis = dream.analysis is not None
    
    return response_data


@router.put("/{dream_id}", response_model=DreamResponse)
async def update_dream_endpoint(
    dream_id: UUID,
    dream_data: DreamUpdate,
    current_user: VerifiedUser,
    db: DatabaseSession
):
    """
    Обновить сон
    
    - Можно обновить title, content, emoji, comment
    """
    dream = await get_dream_by_id(db, dream_id, current_user)
    
    if not dream:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dream not found"
        )
    
    try:
        updated_dream = await update_dream(db, dream, dream_data)
        
        response_data = DreamResponse.model_validate(updated_dream)
        response_data.has_analysis = updated_dream.analysis is not None
        
        return response_data
    
    except Exception as e:
        logger.error(f"Failed to update dream: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update dream"
        )


@router.delete("/{dream_id}", response_model=MessageResponse)
async def delete_dream_endpoint(
    dream_id: UUID,
    current_user: VerifiedUser,
    db: DatabaseSession
):
    """
    Удалить сон
    
    - Удаляет сон и все связанные данные (анализ)
    - Удаляет обложку из S3 если она есть
    """
    dream = await get_dream_by_id(db, dream_id, current_user)
    
    if not dream:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dream not found"
        )
    
    try:
        # Удаляем обложку из S3 если есть
        if dream.cover_url:
            try:
                storage_service.delete_file(dream.cover_url)
            except Exception as e:
                logger.warning(f"Failed to delete cover from S3: {e}")
        
        # Удаляем сон
        await delete_dream(db, dream)
        
        return {"message": "Dream successfully deleted"}
    
    except Exception as e:
        logger.error(f"Failed to delete dream: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete dream"
        )


@router.post("/{dream_id}/cover", response_model=DreamResponse)
async def upload_dream_cover(
    dream_id: UUID,
    current_user: VerifiedUser,
    db: DatabaseSession,
    file: UploadFile = File(...)
):
    """
    Загрузить обложку для сна
    
    - Поддерживаются форматы: JPEG, PNG
    - Максимальный размер: 5MB
    """
    dream = await get_dream_by_id(db, dream_id, current_user)
    
    if not dream:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dream not found"
        )
    
    # Проверяем тип файла
    if file.content_type not in ["image/jpeg", "image/png"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only JPEG and PNG images are supported"
        )
    
    # Читаем файл
    file_content = await file.read()
    
    # Проверяем размер файла (5MB)
    if len(file_content) > 5 * 1024 * 1024:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="File size exceeds 5MB limit"
        )
    
    try:
        # Удаляем старую обложку если есть
        if dream.cover_url:
            try:
                storage_service.delete_file(dream.cover_url)
            except Exception as e:
                logger.warning(f"Failed to delete old cover: {e}")
        
        # Загружаем новую обложку
        cover_url = storage_service.upload_file(
            file_content=file_content,
            file_name=file.filename,
            content_type=file.content_type
        )
        
        # Обновляем сон
        dream.cover_url = cover_url
        await db.commit()
        await db.refresh(dream)
        
        response_data = DreamResponse.model_validate(dream)
        response_data.has_analysis = dream.analysis is not None
        
        return response_data
    
    except Exception as e:
        logger.error(f"Failed to upload cover: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to upload cover"
        )

