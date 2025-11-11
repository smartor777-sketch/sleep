"""HTTP клиент для взаимодействия с LLM Service"""

import logging
import httpx

from config import settings

logger = logging.getLogger(__name__)


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
        gpt_role: str,
        user_description: str | None = None
    ) -> str:
        """
        Отправить запрос на анализ сна в LLM Service
        
        Args:
            dream_text: Текст сна
            gpt_role: Роль ('psychological' или 'esoteric')
            user_description: Описание пользователя (опционально)
        
        Returns:
            Результат анализа
        
        Raises:
            Exception: При ошибке запроса
        """
        url = f"{self.base_url}/analyze"
        
        payload = {
            "dream_text": dream_text,
            "gpt_role": gpt_role,
            "user_description": user_description
        }
        
        logger.info(f"Sending analysis request to LLM Service: {url}")
        logger.debug(f"Payload: role={gpt_role}, text_length={len(dream_text)}")
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(url, json=payload)
                response.raise_for_status()
                
                data = response.json()
                result = data.get("result")
                
                if not result:
                    raise ValueError("Empty result from LLM Service")
                
                logger.info(f"Successfully received analysis, length: {len(result)} chars")
                return result
        
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error from LLM Service: {e.response.status_code} - {e.response.text}")
            raise Exception(f"LLM Service error: {e.response.status_code}")
        
        except httpx.RequestError as e:
            logger.error(f"Request error to LLM Service: {e}")
            raise Exception("Failed to connect to LLM Service")
        
        except Exception as e:
            logger.error(f"Unexpected error calling LLM Service: {e}")
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

