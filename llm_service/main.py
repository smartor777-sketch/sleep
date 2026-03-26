"""LLM Service - Микросервис для анализа снов с помощью LLM"""

import json
import logging
import re
from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel, Field

from config import settings
from providers.gonka_proxy import GonkaProxyProvider
from providers.comet_api import CometApiProvider
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
llm_provider = GonkaProxyProvider(
    base_url=settings.gonka_base_url,
    api_key=settings.gonka_api_key.get_secret_value(),
    model=settings.gonka_model,
)

# Инициализация fallback-провайдера (опционально)
fallback_provider: CometApiProvider | None = None
if settings.comet_api_key:
    fallback_provider = CometApiProvider(
        api_key=settings.comet_api_key.get_secret_value(),
        model=settings.comet_model,
        base_url=settings.comet_base_url,
    )
    logger.info("CometAPI fallback provider initialized")


# Pydantic модели
class AnalyzeRequest(BaseModel):
    """Запрос на анализ сна"""
    dream_text: str = Field(..., min_length=10, max_length=10000, description="Текст сна")
    user_description: str | None = Field(None, max_length=1000, description="Описание пользователя (опционально)")
    user_memory_md: str | None = Field(None, max_length=5000, description="User psychological profile markdown")


class AnalyzeResponse(BaseModel):
    analysis_text: str = Field(..., description="Markdown-анализ сна")
    title: str | None = Field(None, max_length=64, description="Короткий заголовок сна")
    gradient: dict | None = Field(None, description="Цвета градиента: color1, color2")
    archetypes_delta: dict[str, int] = Field(default_factory=dict, description="Дельта архетипов")
    symbol_entities: list[dict] = Field(default_factory=list, description="Список symbol entities")
    memory_update: dict | None = Field(None, description="Diff for user psychological profile")


class ChatMessage(BaseModel):
    """Одно сообщение чата"""
    role: str = Field(..., description="Роль: system, user, assistant")
    text: str = Field(..., description="Текст сообщения")


class ChatRequest(BaseModel):
    """Запрос на мульти-тёрн чат"""
    messages: list[ChatMessage] = Field(..., min_length=1, description="Массив сообщений")
    user_memory_md: str | None = Field(None, max_length=5000, description="User psychological profile (read-only context)")


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
            dream_text=request.dream_text,
            user_memory_md=request.user_memory_md,
        )
        temperature = get_default_temperature()
        
        # Вызываем LLM provider (с fallback на CometAPI)
        try:
            result = await llm_provider.analyze_dream(
                dream_text=request.dream_text,
                system_prompt=system_prompt,
                temperature=temperature,
            )
        except Exception as primary_err:
            if fallback_provider is None:
                raise
            logger.warning("Primary provider failed, trying CometAPI fallback: %s", primary_err)
            result = await fallback_provider.analyze_dream(
                dream_text=request.dream_text,
                system_prompt=system_prompt,
                temperature=temperature,
            )
            logger.info("CometAPI fallback succeeded for /analyze")

        payload = _extract_json(result)
        if payload is None:
            payload = {"analysis_text": result, "archetypes_delta": {}}

        # Hard constraints for downstream storage
        title = payload.get("title")
        if isinstance(title, str):
            payload["title"] = title.strip()[:64] or None
        else:
            payload["title"] = None

        gradient = payload.get("gradient")
        if not isinstance(gradient, dict):
            payload["gradient"] = None

        delta = payload.get("archetypes_delta")
        if not isinstance(delta, dict):
            payload["archetypes_delta"] = {}
        else:
            normalized = {}
            for k, v in delta.items():
                key = str(k).strip()
                if not key:
                    continue
                try:
                    iv = int(v)
                except Exception:
                    continue
                if iv > 0:
                    normalized[key] = iv
            payload["archetypes_delta"] = normalized

        if not payload.get("analysis_text"):
            payload["analysis_text"] = result
        payload["symbol_entities"] = _normalize_symbol_entities(payload.get("symbol_entities"))

        # Pass through memory_update if present
        memory_update = payload.get("memory_update")
        if isinstance(memory_update, dict):
            payload["memory_update"] = memory_update
        else:
            payload["memory_update"] = None

        logger.info(
            "Successfully analyzed dream: text=%s title=%s archetypes=%s symbol_entities=%s",
            len(payload["analysis_text"]),
            bool(payload.get("title")),
            len(payload.get("archetypes_delta", {})),
            len(payload.get("symbol_entities", [])),
        )

        return payload
    
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
    пробрасывает в LLM provider и возвращает ответ.
    """
    try:
        logger.info(f"Received chat request with {len(request.messages)} messages")

        messages = [{"role": m.role, "content": m.text} for m in request.messages]

        try:
            result = await llm_provider.chat_completion(
                messages=messages,
                temperature=get_default_temperature(),
            )
        except Exception as primary_err:
            if fallback_provider is None:
                raise
            logger.warning("Primary provider failed, trying CometAPI fallback: %s", primary_err)
            result = await fallback_provider.chat_completion(
                messages=messages,
                temperature=get_default_temperature(),
            )
            logger.info("CometAPI fallback succeeded for /chat")

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


def _extract_json(raw: str) -> dict | None:
    """Extract first valid JSON object from raw model output."""
    text = raw.strip()
    if not text:
        return None
    try:
        obj = json.loads(text)
        return obj if isinstance(obj, dict) else None
    except Exception:
        pass

    fence_start = text.find("{")
    fence_end = text.rfind("}")
    if fence_start == -1 or fence_end == -1 or fence_end <= fence_start:
        return None
    candidate = text[fence_start:fence_end + 1]
    try:
        obj = json.loads(candidate)
        return obj if isinstance(obj, dict) else None
    except Exception:
        return None


_ENTITY_WORD_RE = re.compile(r"[A-Za-zА-Яа-яЁё-]{3,}", re.UNICODE)
_ENTITY_STOPWORDS = {
    "того", "где", "чуть", "есть", "находит", "находить", "следующий", "следующая", "следующее",
    "типа", "кстати", "потом", "вроде", "сон", "сны", "сна", "сне", "это", "как", "что",
    "когда", "или", "для", "there", "then", "where", "what", "this", "that", "dream",
    "людей", "люди", "человек", "компании", "компания", "каких", "какой", "какая", "какие",
    "возможно", "возможный", "возможная", "возможные", "эльфов", "эльфы", "фей", "фея", "феи",
}
_ALLOWED_ENTITY_TYPES = {"symbol", "place", "figure", "object", "motif", "event"}


def _normalize_symbol_entities(raw: object, limit: int = 20) -> list[dict]:
    if not isinstance(raw, list):
        return []
    normalized: list[dict] = []
    seen_keys: set[tuple[str, str]] = set()

    for item in raw:
        if len(normalized) >= limit:
            break
        if not isinstance(item, dict):
            continue
        canonical = _normalize_token(str(item.get("canonical_name") or ""))
        if not canonical:
            continue
        label = _normalize_label(str(item.get("display_label") or ""))
        if not label:
            label = f"образ {canonical}"
        if len(label.split()) < 2:
            label = f"образ {canonical}"

        key = (canonical, label)
        if key in seen_keys:
            continue
        seen_keys.add(key)

        entity_type = str(item.get("entity_type") or "symbol").strip().lower()
        if entity_type not in _ALLOWED_ENTITY_TYPES:
            entity_type = "symbol"

        try:
            weight = float(item.get("weight", 1.0))
        except Exception:
            weight = 1.0
        weight = max(0.05, min(1.0, weight))

        source_indexes = []
        raw_indexes = item.get("source_chunk_indexes")
        if isinstance(raw_indexes, list):
            for idx in raw_indexes:
                try:
                    iv = int(idx)
                except Exception:
                    continue
                if iv >= 0:
                    source_indexes.append(iv)
        source_indexes = sorted(set(source_indexes))[:12]

        related_archetypes = []
        raw_archetypes = item.get("related_archetypes")
        if isinstance(raw_archetypes, list):
            for archetype in raw_archetypes:
                name = str(archetype or "").strip()
                if name:
                    related_archetypes.append(name)
        related_archetypes = list(dict.fromkeys(related_archetypes))[:6]

        normalized.append(
            {
                "canonical_name": canonical,
                "display_label": label,
                "entity_type": entity_type,
                "weight": weight,
                "source_chunk_indexes": source_indexes,
                "related_archetypes": related_archetypes,
            }
        )

    return normalized


def _normalize_label(value: str) -> str:
    words: list[str] = []
    for match in _ENTITY_WORD_RE.finditer((value or "").lower()):
        token = _normalize_token(match.group(0))
        if token:
            words.append(token)
    if not words:
        return ""
    return " ".join(words[:3])


def _normalize_token(value: str) -> str:
    token = (value or "").strip().lower()
    if not token:
        return ""
    if token in _ENTITY_STOPWORDS:
        return ""
    if token.isdigit() or len(token) < 3:
        return ""
    return token
