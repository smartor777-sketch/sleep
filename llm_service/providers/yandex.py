"""Провайдер для YandexGPT"""

import logging
from yandex_cloud_ml_sdk import YCloudML

logger = logging.getLogger(__name__)


class YandexGPTProvider:
    """Провайдер для работы с YandexGPT"""
    
    def __init__(self, folder_id: str, api_key: str):
        """
        Инициализация провайдера
        
        Args:
            folder_id: Folder ID из Yandex Cloud
            api_key: API ключ
        """
        self.folder_id = folder_id
        self.api_key = api_key
        self.sdk = YCloudML(
            folder_id=folder_id,
            auth=api_key,
        )
    
    async def analyze_dream(
        self,
        dream_text: str,
        system_prompt: str,
        temperature: float = 0.5
    ) -> str:
        """
        Анализ сна с помощью YandexGPT
        
        Args:
            dream_text: Текст сна для анализа
            system_prompt: Системный промпт (роль)
            temperature: Temperature для генерации (0.0-1.0)
        
        Returns:
            Результат анализа от нейросети
        
        Raises:
            Exception: При ошибке вызова API
        """
        messages = [
            {
                "role": "system",
                "text": system_prompt
            },
            {
                "role": "user",
                "text": dream_text
            }
        ]
        
        logger.info(f"Requesting YandexGPT with temperature={temperature}")
        logger.debug(f"System prompt: {system_prompt[:100]}...")
        logger.debug(f"Dream text length: {len(dream_text)} chars")
        
        try:
            result = (
                self.sdk.models.completions("yandexgpt")
                .configure(temperature=temperature)
                .run(messages)
            )
            
            # Возвращаем первый вариант ответа
            if result and len(result) > 0:
                logger.info("Successfully received response from YandexGPT")
                return result[0].text if hasattr(result[0], 'text') else str(result[0])
            else:
                logger.error("Empty response from YandexGPT")
                raise ValueError("Empty response from YandexGPT")
        
        except Exception as e:
            logger.error(f"Error calling YandexGPT: {e}")
            raise

