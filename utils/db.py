import asyncpg
import logging

from datetime import datetime
from asyncpg import Connection
from pytz import timezone

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
async def db_start():

    conn: Connection = await get_conn()
    await conn.execute(
        "CREATE TABLE IF NOT EXISTS users("
        "user_id BIGINT PRIMARY KEY,"  # Уникальный идентификатор пользователя
        "username VARCHAR(32),"  # Имя пользователя
        "first_name VARCHAR(64),"  # Имя пользователя
        "reg_time INT,"  # Время регистрации в формате timestamp
        "inviter VARCHAR(32),"  # ID пригласившего пользователя
        "sub_time TIMESTAMP DEFAULT NULL,"  # Время начала подписки
        "sub_type VARCHAR(16) DEFAULT 'none',"  # Тип подписки - месяц, 3, полгода
        "last_analyze TIMESTAMP DEFAULT NOW(),"  # Последнее использование анализа
        "self_description VARCHAR(512) DEFAULT 'none',"  # Общие пояснения ко Снам 
        "gpt_role VARCHAR(16) DEFAULT 'psychological',"  # Роль нейросети
        "ticket VARCHAR(4096))"
    )

    await conn.execute(
        "CREATE TABLE IF NOT EXISTS dreams("
        "id SERIAL PRIMARY KEY,"  # Уникальный идентификатор записи
        "user_id BIGINT,"  # Идентификатор пользователя
        "title VARCHAR(64),"  # Заголовок
        "content VARCHAR(4096),"  # Основное содержание записи
        "emoji VARCHAR(4) DEFAULT '',"  # Эмодзи записи
        "comment VARCHAR(128) DEFAULT '',"  # Комментарий к записи
        "cover VARCHAR(128) DEFAULT '',"  # Обложка
        "create_time TIMESTAMP WITH TIME ZONE DEFAULT NOW())"  # Время создания записи 
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

    conn = await get_conn()
    row = await conn.fetchrow("SELECT * FROM users WHERE user_id = $1", user_id)
    await conn.close()
    return row


# Регистрация нового пользователя после проверки подписки
async def add_user(payload: str, 
                   user_id: str | int, 
                   username: str, 
                   first_name: str):

    conn = await get_conn()
    await conn.execute(
        "INSERT INTO users(user_id, username, first_name, reg_time, inviter) VALUES ($1, $2, $3, $4, $5)",
        user_id, username, first_name, int(datetime.now().timestamp()), payload
    )
    await conn.close()


# Запись нового Сна
async def create_dream(user_id: str | int, 
                       content: str):
    
    conn = await get_conn()
    try:
        moscow_tz = timezone('Europe/Moscow')
        create_time = datetime.now(moscow_tz)
        
        # Записываем сон в базу
        await conn.execute(
            "INSERT INTO dreams(user_id, title, content, create_time) VALUES ($1, $2, $3, $4)",
            user_id, str(content[:16] + '...'), content, create_time
        )
    finally:
        await conn.close()


# Удаление Ана
async def delete_dream(dream_id: int):
    
    conn = await get_conn()
    try:
        await conn.execute(
            "DELETE FROM dreams WHERE id = $1",
            dream_id
        )
    finally:
        await conn.close()


# Получения словаря Снов за месяц и сохранение его в кэш
async def load_month(user_id: int, year: int, month: int):
    """
    Загружает сны за указанный месяц и кэширует их по дням как список кортежей.
    """
    conn = await get_conn()
    try:
        # Выполняем запрос и получаем все строки
        dreams = await conn.fetch(
            "SELECT id, title, content, emoji, comment, cover, create_time FROM dreams "
            "WHERE user_id = $1 AND DATE_PART('year', create_time) = $2 AND DATE_PART('month', create_time) = $3",
            user_id, year, month
        )
        from utils import cache_object, clear_cache

        # Очищаем кэш
        clear_cache(user_id)

        # Группируем записи по дням
        for dream in dreams:
            # Преобразуем Record в кортеж значений
            dream_tuple = tuple(dream)
            dream_id, title, content, emoji, comment, cover, create_time = dream_tuple
            day = str(create_time.day)

            if day not in cache_object[user_id]:
                cache_object[user_id][day] = []
            cache_object[user_id][day].append(dream_tuple)
    finally:
        # Закрываем соединение
        await conn.close()


# Редактирование содержания Сна
async def update_content(new_content: str,
                         dream_id: int,
                         user_id: int | str):
    
    conn = await get_conn()

    await conn.execute(
        "UPDATE dreams SET content = $1 WHERE id = $2 AND user_id = $3",
        new_content, dream_id, user_id
    )
    await conn.close()


# Редактирование заголовка Сна
async def update_title(new_title: str,
                       dream_id: int,
                       user_id: int | str):
    
    conn = await get_conn()
    await conn.execute(
        "UPDATE dreams SET title = $1 WHERE id = $2 AND user_id = $3",
        new_title, dream_id, user_id
    )
    await conn.close()


# Редактирование комментария Сна
async def update_comment(new_comment: str,
                         dream_id: int,
                         user_id: int | str):
    
    conn = await get_conn()
    await conn.execute(
        "UPDATE dreams SET comment = $1 WHERE id = $2 AND user_id = $3",
        new_comment, dream_id, user_id
    )
    await conn.close()


# Редактирование обложки Сна
async def update_cover(new_cover: str,
                       dream_id: int,
                       user_id: int | str):
    
    conn = await get_conn()
    await conn.execute(
        "UPDATE dreams SET cover = $1 WHERE id = $2 AND user_id = $3",
        new_cover, dream_id, user_id
    )
    await conn.close()


# Редактирование эмодзи Сна
async def update_emoji(new_emoji: str,
                       dream_id: int,
                       user_id: int):
    
    conn = await get_conn()
    await conn.execute(
        "UPDATE dreams SET emoji = $1 WHERE id = $2 AND user_id = $3",
        new_emoji, dream_id, user_id
    )
    await conn.close()


# Редактирование обращения в тех.поддержку
async def update_ticket(new_ticket: str,
                        user_id: int):
    
    conn = await get_conn()
    await conn.execute(
        "UPDATE users SET ticket = $1 WHERE user_id = $2",
        new_ticket, user_id
    )
    await conn.close()


async def delete_ticket(user_id: int):

    conn = await get_conn()
    try:
        await conn.execute(
            "UPDATE users SET ticket = NULL WHERE user_id = $1",
            user_id
        )
    finally:
        await conn.close()


# Редактирование описания себя
async def update_self_description(new_description: str,
                                  user_id: int):
    
    conn = await get_conn()
    await conn.execute(
        "UPDATE users SET self_description = $1 WHERE user_id = $2",
        new_description, user_id
    )
    await conn.close()


# Редактирование роли GPT
async def update_role(new_role: str,
                      user_id: int):
    
    conn = await get_conn()
    await conn.execute(
        "UPDATE users SET gpt_role = $1 WHERE user_id = $2",
        new_role, user_id
    )
    await conn.close()


async def get_user_stats(user_id: int):
    """
    Возвращает статистику пользователя:
    - Имя, время регистрации, пригласивший, подписка.
    - Количество снов.
    - Количество оплат и их сумма.
    """
    conn = await get_conn()  # Получаем соединение
    try:
        # Получаем данные из таблицы users
        user_data = await conn.fetchrow(
            "SELECT first_name, reg_time, inviter, sub_time, sub_type, gpt_role FROM users WHERE user_id = $1",
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

    finally:
        await conn.close()  # Закрываем соединение вручную

    # Форматируем данные
    stats = {
        "first_name": user_data["first_name"] if user_data else "Неизвестно",
        "reg_time": datetime.fromtimestamp(user_data["reg_time"]).strftime("%Y-%m-%d %H:%M") if user_data and user_data["reg_time"] else "Неизвестно",
        "inviter": user_data["inviter"] if user_data and user_data["inviter"] else "Нет",
        "sub_time": user_data["sub_time"].strftime("%Y-%m-%d %H:%M") if user_data and user_data["sub_time"] else "Нет",
        "sub_type": user_data["sub_type"] if user_data and user_data["sub_type"] else "Нет",
        "gpt_role": user_data["gpt_role"],
        "dreams_count": dreams_count,
        "orders_count": orders_count,
        "orders_total": orders_total if orders_total != None else 0
    }

    return stats

async def get_last_10_dreams(user_id: int):
    """
    Возвращает последние 10 записей снов пользователя.
    """
    conn = await get_conn()  # Получаем соединение
    try:
        dreams = await conn.fetch(
            "SELECT content FROM dreams WHERE user_id = $1 ORDER BY create_time DESC LIMIT 10",
            user_id
        )
        return [dream["content"] for dream in dreams]
    finally:
        await conn.close()  # Закрываем соединение вручную


async def update_last_analyze(user_id: int):
    """
    Обновляет колонку last_analyze в таблице users на текущее время (без часового пояса).
    
    Args:
        user_id (int): ID пользователя, для которого обновляется время последнего анализа.
    """
    from datetime import datetime, timezone  # Импорт внутри функции для изоляции
    conn = await get_conn()
    try:
        current_time_with_tz = datetime.now(timezone.utc)  # offset-aware
        current_time = current_time_with_tz.replace(tzinfo=None)  # убираем часовой пояс
        logger.info(f"Updating last_analyze for user {user_id} to {current_time}")
        await conn.execute(
            "UPDATE users SET last_analyze = $1 WHERE user_id = $2",
            current_time, user_id
        )
    except Exception as e:
        logger.error(f"Failed to update last_analyze for user {user_id}: {e}")
        raise
    finally:
        await conn.close()


async def get_service_stats() -> dict:
    """
    Возвращает общую статистику по сервису.
    """
    conn = await get_conn()
    try:
        users_count = await conn.fetchval("SELECT COUNT(*) FROM users")
        dreams_count = await conn.fetchval("SELECT COUNT(*) FROM dreams")
        orders_stats = await conn.fetchrow(
            "SELECT COUNT(*), SUM(amount) FROM orders WHERE pay_time IS NOT NULL"
        )
        orders_count = orders_stats['count'] if orders_stats else 0
        total_amount = orders_stats['sum'] if orders_stats and orders_stats['sum'] is not None else 0

        stats = {
            "users_count": users_count or 0,
            "dreams_count": dreams_count or 0,
            "orders_count": orders_count,
            "total_amount": total_amount
        }
        return stats
    finally:
        await conn.close()