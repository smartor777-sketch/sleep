"""LLM Service - Микросервис для анализа снов с помощью LLM"""

import logging
from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel, Field

from config import settings
from providers.yandex import YandexGPTProvider
from prompts import get_analysis_prompt, get_default_temperature, get_chat_system_prompt

# Настройка логирования
logging.basicConfig(
    level=getattr(logging, settings.log_level),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Инициализация FastAPI
app = FastAPI(
    title="JungAI LLM Service",
    description="Сервис для анализа снов с помощью нейросетей",
    version="1.0.0"
)

# Инициализация провайдера
yandex_provider = YandexGPTProvider(
    folder_id=settings.yandex_folder_id,
    api_key=settings.yandex_api_key.get_secret_value()
)


# Pydantic модели
class AnalyzeRequest(BaseModel):
    """Запрос на анализ сна"""
    dream_text: str = Field(..., min_length=10, max_length=10000, description="Текст сна")
    user_description: str | None = Field(None, max_length=1000, description="Описание пользователя (опционально)")


class AnalyzeResponse(BaseModel):
    """Ответ с результатом анализа"""
    result: str = Field(..., description="Результат анализа от нейросети")


class ChatMessage(BaseModel):
    """Одно сообщение чата"""
    role: str = Field(..., description="Роль: system, user, assistant")
    text: str = Field(..., description="Текст сообщения")


class ChatRequest(BaseModel):
    """Запрос на мульти-тёрн чат"""
    messages: list[ChatMessage] = Field(..., min_length=1, description="Массив сообщений")


class ChatResponse(BaseModel):
    """Ответ чата"""
    result: str = Field(..., description="Ответ от нейросети")


class HealthResponse(BaseModel):
    """Статус сервиса"""
    status: str
    service: str
    version: str


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Проверка здоровья сервиса"""
    return {
        "status": "ok",
        "service": "llm_service",
        "version": "1.0.0"
    }


@app.post("/analyze", response_model=AnalyzeResponse, status_code=status.HTTP_200_OK)
async def analyze_dream(request: AnalyzeRequest):
    """
    Анализ сна с помощью LLM
    
    Args:
        request: Запрос с текстом сна, ролью и описанием пользователя
    
    Returns:
        Результат анализа
    
    Raises:
        HTTPException: При ошибке анализа
    """
    try:
        logger.info("Received analysis request")
        
        # Получаем промпт и temperature
        system_prompt = get_analysis_prompt(
            user_description=request.user_description,
            dream_text=request.dream_text
        )
        temperature = get_default_temperature()
        
        # Вызываем YandexGPT
        result = await yandex_provider.analyze_dream(
            dream_text=request.dream_text,
            system_prompt=system_prompt,
            temperature=temperature
        )
        
        logger.info(f"Successfully analyzed dream, result length: {len(result)} chars")
        
        return {"result": result}
    
    except ValueError as e:
        logger.error(f"Validation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    
    except Exception as e:
        logger.error(f"Error during analysis: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to analyze dream. Please try again later."
        )


@app.post("/chat", response_model=ChatResponse, status_code=status.HTTP_200_OK)
async def chat(request: ChatRequest):
    """
    Мульти-тёрн чат с контекстом всех снов.

    Принимает массив сообщений (system + user + assistant + ...),
    пробрасывает в YandexGPT и возвращает ответ.
    """
    try:
        logger.info(f"Received chat request with {len(request.messages)} messages")

        messages = [{"role": m.role, "text": m.text} for m in request.messages]

        result = await yandex_provider.chat_completion(
            messages=messages,
            temperature=get_default_temperature(),
        )

        logger.info(f"Chat response length: {len(result)} chars")
        return {"result": result}

    except ValueError as e:
        logger.error(f"Validation error in chat: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

    except Exception as e:
        logger.error(f"Error during chat: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process chat request. Please try again later."
        )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        reload=True,
        log_level=settings.log_level.lower()
    )

