from collections import defaultdict

# Глобальный кэш для хранения данных пользователей
cache = defaultdict(dict)


# Очищает кэш для пользователя
def clear_cache(user_id: int):
    if user_id in cache:
        del cache[user_id]


# Возвращает кэш для пользователя
def get_cache(user_id: int):
    return cache.get(user_id, {})


# Обновляет кэш для пользователя
def update_cache(user_id: int, data: dict):
    cache[user_id] = data