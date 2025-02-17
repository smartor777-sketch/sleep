import asyncpg
import logging

from datetime import datetime, date, time, timedelta
from typing import Dict, Any
from asyncpg import Connection

from config import DB_USER, DB_HOST, DB_DATABASE, DB_PASSWORD
from utils import cache


logger = logging.getLogger(__name__)

logging.basicConfig(
    level=logging.INFO,
    format='%(filename)s:%(lineno)d #%(levelname)-8s '
           '[%(asctime)s] - %(name)s - %(message)s')


# Функция для установления соединения с базой данных
async def get_conn() -> Connection:
    return await asyncpg.connect(user=DB_USER, password=DB_PASSWORD, database=DB_DATABASE, host=DB_HOST)


# Функция для создания необходимых таблиц в базе данных, если они еще не существуют
async def start():

    conn: Connection = await get_conn()
    await conn.execute(
        "CREATE TABLE IF NOT EXISTS users("
        "user_id BIGINT PRIMARY KEY,"  # Уникальный идентификатор пользователя
        "username VARCHAR(32),"  # Имя пользователя
        "first_name VARCHAR(64),"  # Имя пользователя
        "reg_time INT,"  # Время регистрации в формате timestamp
        "inviter VARCHAR(32),"  # ID пригласившего пользователя
        "sub_time TIMESTAMP DEFAULT NOW(),"  # Время начала подписки
        "sub_type VARCHAR(16) DEFAULT 'none'"  # Тип подписки - месяц, 3, полгода
    )

    await conn.execute(
        "CREATE TABLE IF NOT EXISTS dreams("
        "id SERIAL PRIMARY KEY,"  # Уникальный идентификатор записи
        "user_id BIGINT,"  # Идентификатор пользователя
        "title VARCHAR(64),"  # Заголовок
        "content VARCHAR(1024),"  # Основное содержание записи
        "emoji VARCHAR(4) DEFAULT '',"  # Эмодзи записи
        "comment VARCHAR(128) DEFAULT '',"  # Комментарий к записи
        "cover VARCHAR(128) DEFAULT '',"  # Обложка
        "create_time TIMESTAMP DEFAULT NOW()"  # Время создания записи 
    )

    await conn.execute(
        "CREATE TABLE IF NOT EXISTS orders("
        "id SERIAL PRIMARY KEY,"  # Уникальный идентификатор заказа
        "user_id BIGINT,"  # ID пользователя
        "amount INT,"  # Сумма покупки
        "create_time TIMESTAMP DEFAULT NOW(),"  # Время создания заказа
        "pay_time TIMESTAMP)"  # Время оплаты заказа
    )


# Получение user по user_id
async def get_user(user_id: str | int):

    conn: Connection = await get_conn()
    row = await conn.fetchrow("SELECT * FROM users WHERE user_id = $1", user_id)
    await conn.close()
    return row


# Регистрация нового пользователя после проверки подписки
async def add_user(payload: str, 
                   user_id: str | int, 
                   username: str, 
                   first_name: str):

    conn: Connection = await get_conn()
    await conn.execute(
        "INSERT INTO users(user_id, username, first_name, reg_time, inviter) VALUES ($1, $2, $3, $4, $5)",
        user_id, username, first_name, int(datetime.now().timestamp()), payload
    )
    await conn.close()


# Запись нового Сна
async def create_dream(user_id: str | int, 
                       content: str):
    
    conn: Connection = await get_conn()
    await conn.execute(
        "INSERT INTO dreams(user_id, title, content) VALUES ($1, $2, $3)",
        user_id, str(content[:16] + '...'), content
    )
    await conn.close()


# Получения словаря Снов за месяц и сохранение его в кэш
async def load_month(user_id: int, 
                     year: int, 
                     month: int):

    conn: Connection = await get_conn()
    try:
        # Выполняем запрос и получаем все строки
        dreams = await conn.fetch(
            "SELECT id, title, content, emoji, comment, cover, create_time FROM dreams "
            "WHERE user_id = $1 AND DATE_PART('year', create_time) = $2 AND DATE_PART('month', create_time) = $3",
            user_id, year, month
        )
        
        # Группируем записи по дням
        for dream in dreams:
            dream_id, title, content, emoji, comment, cover, create_time = dream
            day = create_time.day

            logger.info(f"Getting dream from DB: {dream}, day: {day}")
            
            if day not in cache[user_id]:
                cache[user_id][day] = []
            cache[user_id][day].append(dream)
    finally:
        # Закрываем соединение
        await conn.close()


# Редактирование содержания Сна
async def update_content(new_content: str,
                         dream_id: int,
                         user_id: int | str):
    
    conn: Connection = await get_conn()

    await conn.execute(
        "UPDATE dreams SET content = $1 WHERE id = $2 AND user_id = $3",
        new_content, dream_id, user_id
    )
    await conn.close()


# Редактирование заголовка Сна
async def update_title(new_title: str,
                       dream_id: int,
                       user_id: int | str):
    
    conn: Connection = await get_conn()
    await conn.execute(
        "UPDATE dreams SET title = $1 WHERE id = $2 AND user_id = $3",
        new_title, dream_id, user_id
    )
    await conn.close()


# Редактирование комментария Сна
async def update_comment(new_comment: str,
                         dream_id: int,
                         user_id: int | str):
    
    conn: Connection = await get_conn()
    await conn.execute(
        "UPDATE dreams SET comment = $1 WHERE id = $2 AND user_id = $3",
        new_comment, dream_id, user_id
    )
    await conn.close()


# Редактирование обложки Сна
async def update_cover(new_cover: str,
                       dream_id: int,
                       user_id: int | str):
    
    conn: Connection = await get_conn()
    await conn.execute(
        "UPDATE dreams SET cover = $1 WHERE id = $2 AND user_id = $3",
        new_cover, dream_id, user_id
    )
    await conn.close()


# Редактирование эмодзи Сна
async def update_emoji(new_emoji: str,
                       dream_id: int,
                       user_id: int | str):
    
    conn: Connection = await get_conn()
    await conn.execute(
        "UPDATE dreams SET emoji = $1 WHERE id = $2 AND user_id = $3",
        new_emoji, dream_id, user_id
    )
    await conn.close()