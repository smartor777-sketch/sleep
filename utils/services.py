import speech_recognition as sr
import os
import tempfile
import emoji

from collections import Counter
from pydub import AudioSegment

from utils import get_cache


def is_emoji(text: str) -> bool:
    return bool(emoji.emoji_count(text))


def day_emoji(user_id: int, day: int) -> str:
    """
    Возвращает самый частый эмодзи для указанного дня.
    Если записей нет или у них нет эмодзи, возвращает пустую строку.
    """
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