import asyncpg
import logging

from datetime import datetime
from asyncpg import Connection

from utils import cache
from config import get_config, DbConfig

database = get_config(DbConfig, 'database')
DB_USER = database.user
DB_PASSWORD = database.password.get_secret_value()
DB_DATABASE = database.database
DB_HOST = database.host

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


async def get_user_stats(user_id: int):
    """
    Возвращает статистику пользователя:
    - Имя, время регистрации, пригласивший, подписка.
    - Количество снов.
    - Количество оплат и их сумма.
    """
    async with await get_conn() as conn:
        # Получаем данные из таблицы users
        user_data = await conn.fetchrow(
            "SELECT first_name, reg_time, inviter, sub_time, sub_type FROM users WHERE user_id = $1",
            user_id
        )

        # Получаем количество снов
        dreams_count = await conn.fetchval(
            "SELECT COUNT(*) FROM dreams WHERE user_id = $1",
            user_id
        )

        # Получаем количество оплат и их сумму
        orders_data = await conn.fetchrow(
            "SELECT COUNT(*), SUM(amount) FROM orders WHERE user_id = $1 AND pay_time IS NOT NULL",
            user_id
        )
        orders_count, orders_total = orders_data if orders_data else (0, 0)

    # Форматируем данные
    stats = {
        "first_name": user_data["first_name"] if user_data else "Неизвестно",
        "reg_time": datetime.fromtimestamp(user_data["reg_time"]).strftime("%Y-%m-%d %H:%M") if user_data and user_data["reg_time"] else "Неизвестно",
        "inviter": user_data["inviter"] if user_data and user_data["inviter"] else "Нет",
        "sub_time": user_data["sub_time"].strftime("%Y-%m-%d %H:%M") if user_data and user_data["sub_time"] else "Нет",
        "sub_type": user_data["sub_type"] if user_data and user_data["sub_type"] else "Нет",
        "dreams_count": dreams_count,
        "orders_count": orders_count,
        "orders_total": orders_total
    }

    return stats


async def get_last_10_dreams(user_id: int):
    """
    Возвращает последние 10 записей снов пользователя.
    """
    async with await get_conn() as conn:
        dreams = await conn.fetch(
            "SELECT content FROM dreams WHERE user_id = $1 ORDER BY create_time DESC LIMIT 10",
            user_id
        )
    return [dream["content"] for dream in dreams]