import speech_recognition as sr
import os
import tempfile
import emoji

from pydub import AudioSegment


def is_emoji(text: str) -> bool:
    return bool(emoji.emoji_count(text))


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