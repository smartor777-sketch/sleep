"""HTTP клиент для взаимодействия с LLM Service"""

import logging
import httpx
from pydantic import BaseModel, Field, field_validator

from config import settings

logger = logging.getLogger(__name__)
MAX_ANALYZE_USER_DESCRIPTION_LENGTH = 1000


class LLMTransientError(Exception):
    """Retryable upstream/provider failure."""


class LLMPermanentError(Exception):
    """Non-retryable upstream/provider failure."""


class GradientPayload(BaseModel):
    color1: str | None = None
    color2: str | None = None


class SymbolEntityPayload(BaseModel):
    canonical_name: str = Field(..., min_length=1, max_length=128)
    display_label: str = Field(..., min_length=1, max_length=128)
    entity_type: str = Field(default="symbol", max_length=32)
    weight: float = Field(default=1.0, ge=0.0, le=1.0)
    source_chunk_indexes: list[int] = Field(default_factory=list)
    related_archetypes: list[str] = Field(default_factory=list)

    @field_validator("source_chunk_indexes")
    @classmethod
    def _normalize_indexes(cls, value: list[int]) -> list[int]:
        return sorted({int(item) for item in value if int(item) >= 0})[:12]

    @field_validator("related_archetypes")
    @classmethod
    def _normalize_archetypes(cls, value: list[str]) -> list[str]:
        normalized = []
        for item in value:
            text = str(item or "").strip()
            if text:
                normalized.append(text)
        return list(dict.fromkeys(normalized))[:6]


class MemoryUpdateEntry(BaseModel):
    action: str = "replace"
    value: str = ""


class AnalysisPayload(BaseModel):
    analysis_text: str = Field(..., min_length=1)
    title: str | None = Field(None, max_length=64)
    gradient: GradientPayload | None = None
    archetypes_delta: dict[str, int] = Field(default_factory=dict)
    symbol_entities: list[SymbolEntityPayload] = Field(default_factory=list)
    memory_update: dict[str, MemoryUpdateEntry] | None = None


class LLMClient:
    """Клиент для LLM Service"""
    
    def __init__(self, base_url: str = None):
        """
        Инициализация клиента
        
        Args:
            base_url: Базовый URL LLM Service
        """
        self.base_url = base_url or settings.llm_service_url
        self.timeout = 300.0  # 5 минут timeout для LLM запросов
    
    async def analyze_dream(
        self,
        dream_text: str,
        user_description: str | None = None
    ) -> str:
        """
        Отправить запрос на анализ сна в LLM Service
        
        Args:
            dream_text: Текст сна
            user_description: Описание пользователя (опционально)
        
        Returns:
            Результат анализа
        
        Raises:
            Exception: При ошибке запроса
        """
        url = f"{self.base_url}/analyze"
        normalized_user_description = _normalize_user_description(user_description)
        
        payload = {
            "dream_text": dream_text,
            "user_description": normalized_user_description
        }
        
        logger.info(f"Sending analysis request to LLM Service: {url}")
        logger.debug(f"Payload: text_length={len(dream_text)}")
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(url, json=payload)
                response.raise_for_status()
                
                data = response.json()
                result = data.get("result") or data.get("analysis_text")
                
                if not result:
                    raise ValueError("Empty result from LLM Service")
                
                logger.info(f"Successfully received analysis, length: {len(result)} chars")
                return result
        
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error from LLM Service: {e.response.status_code} - {e.response.text}")
            status_code = e.response.status_code
            if status_code == 429 or status_code >= 500:
                raise LLMTransientError(f"LLM Service error: {status_code}") from e
            raise LLMPermanentError(f"LLM Service error: {status_code}") from e
        
        except httpx.RequestError as e:
            logger.error(f"Request error to LLM Service: {e}")
            raise LLMTransientError("Failed to connect to LLM Service") from e
        
        except Exception as e:
            logger.error(f"Unexpected error calling LLM Service: {e}")
            raise

    async def analyze_dream_structured(
        self,
        dream_text: str,
        user_description: str | None = None,
        user_memory_md: str | None = None,
    ) -> AnalysisPayload:
        url = f"{self.base_url}/analyze"
        normalized_user_description = _normalize_user_description(user_description)
        payload = {
            "dream_text": dream_text,
            "user_description": normalized_user_description,
        }
        if user_memory_md:
            payload["user_memory_md"] = user_memory_md

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(url, json=payload)
                response.raise_for_status()
                data = response.json()
                parsed = AnalysisPayload.model_validate(data)
                logger.info("Structured analysis received: title=%s, memory_update=%s",
                           bool(parsed.title), bool(parsed.memory_update))
                return parsed
        except Exception as e:
            logger.warning("Structured analysis failed, fallback to text: %s", e)
            text = await self.analyze_dream(
                dream_text=dream_text,
                user_description=normalized_user_description,
            )
            return AnalysisPayload(analysis_text=text, archetypes_delta={})
    
    async def chat_completion(
        self,
        messages: list[dict],
        user_memory_md: str | None = None,
    ) -> str:
        """
        Отправить массив сообщений в LLM Service /chat

        Args:
            messages: Список сообщений [{role, text}, ...]

        Returns:
            Текст ответа LLM

        Raises:
            Exception: При ошибке запроса
        """
        url = f"{self.base_url}/chat"

        payload = {"messages": messages}
        if user_memory_md:
            payload["user_memory_md"] = user_memory_md

        logger.info(f"Sending chat request to LLM Service: {url}, {len(messages)} messages")

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(url, json=payload)
                response.raise_for_status()

                data = response.json()
                result = data.get("result")

                if not result:
                    raise ValueError("Empty result from LLM Service chat")

                logger.info(f"Successfully received chat response, length: {len(result)} chars")
                return result

        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error from LLM Service chat: {e.response.status_code} - {e.response.text}")
            status_code = e.response.status_code
            if status_code == 429 or status_code >= 500:
                raise LLMTransientError(f"LLM Service chat error: {status_code}") from e
            raise LLMPermanentError(f"LLM Service chat error: {status_code}") from e

        except httpx.RequestError as e:
            logger.error(f"Request error to LLM Service chat: {e}")
            raise LLMTransientError("Failed to connect to LLM Service") from e

        except Exception as e:
            logger.error(f"Unexpected error calling LLM Service chat: {e}")
            raise

    async def health_check(self) -> bool:
        """
        Проверить доступность LLM Service
        
        Returns:
            True если сервис доступен
        """
        url = f"{self.base_url}/health"
        
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(url)
                return response.status_code == 200
        except:
            return False


# Глобальный экземпляр клиента
llm_client = LLMClient()


def _normalize_user_description(value: str | None) -> str | None:
    if value is None:
        return None
    normalized = value.strip()
    if not normalized:
        return None
    if len(normalized) <= MAX_ANALYZE_USER_DESCRIPTION_LENGTH:
        return normalized
    logger.warning(
        "Truncating user_description for /analyze from %s to %s chars",
        len(normalized),
        MAX_ANALYZE_USER_DESCRIPTION_LENGTH,
    )
    return normalized[:MAX_ANALYZE_USER_DESCRIPTION_LENGTH]
