from collections import defaultdict

# Глобальный кэш для хранения данных пользователей
cache_object = defaultdict(dict)


# Очищает кэш для пользователя
def clear_cache(user_id: int):
    if user_id in cache_object:
        del cache_object[user_id]


# Возвращает кэш для пользователя
def get_cache(user_id: int):
    return cache_object.get(user_id, {})


# Обновляет кэш для пользователя
def update_cache(user_id: int, data: dict):
    cache_object[user_id] = data