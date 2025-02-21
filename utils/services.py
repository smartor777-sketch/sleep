import speech_recognition as sr
import os
import tempfile
import emoji
import logging

from collections import Counter
from pydub import AudioSegment
from yandex_cloud_ml_sdk import YCloudML

logger = logging.getLogger(__name__)

logging.basicConfig(
    level=logging.INFO,
    format='%(filename)s:%(lineno)d #%(levelname)-8s '
           '[%(asctime)s] - %(name)s - %(message)s')


async def remove_file(file_path: str):
    try:
        os.remove(file_path)
    except Exception as e:
        logger.error(f"Error removing temp file {file_path}: {e}")


def is_emoji(text: str) -> bool:
    return text in emoji.EMOJI_DATA


def day_emoji(user_id: int, day: int) -> str:
    """
    Возвращает самый частый эмодзи для указанного дня.
    Если записей нет или у них нет эмодзи, возвращает пустую строку.
    """
    from utils import get_cache
    cache = get_cache(user_id)
    if day in cache:
        emojis = [dream[3] for dream in cache[day] if dream[3]]  # Собираем все непустые эмодзи
        if emojis:
            most_common_emoji = Counter(emojis).most_common(1)[0][0]  # Самый частый эмодзи
            return most_common_emoji
    return ""


# Функция для преобразования голосового сообщения в текст
def voice_to_text(file_path):

    recognizer = sr.Recognizer()
    audio = AudioSegment.from_file(file_path)
    
    # Сохраняем аудио как временный wav-файл
    with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp_wav_file:
        audio.export(temp_wav_file.name, format="wav")
        temp_wav_file_path = temp_wav_file.name

    with sr.AudioFile(temp_wav_file_path) as source:
        audio_data = recognizer.record(source)
        
    os.remove(temp_wav_file_path)  # Удаляем временный файл
    
    try:
        text = recognizer.recognize_google(audio_data, language="ru-RU")
        return text
    except sr.UnknownValueError:
        return "Не удалось распознать речь"
    except sr.RequestError:
        return "Ошибка запроса к сервису распознавания"
    

async def analyze_dreams(dreams_text: str, 
                         folder_id: str, 
                         api_key: str):
    """
    Анализирует текст снов с помощью YandexGPT.
    """
    messages = [
        {
            "role": "system",
            "text": "Ты — психолог. Проанализируй сны пользователя и сделай выводы о его эмоциональном состоянии, страхах и желаниях. Будь краток и точен."
        },
        {
            "role": "user",
            "text": dreams_text
        }
    ]

    sdk = YCloudML(
        folder_id=folder_id,
        auth=api_key,
    )

    result = (
        sdk.models.completions("yandexgpt").configure(temperature=0.5).run(messages)
    )

    # Возвращаем первый вариант ответа
    return result[0] if result else "Анализ недоступен."
