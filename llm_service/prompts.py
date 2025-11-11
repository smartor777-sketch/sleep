"""Шаблоны промптов для анализа снов"""


def get_psychological_prompt(user_description: str | None = None) -> str:
    """
    Промпт для психологического анализа (Фрейд, Юнг)
    """
    base_prompt = (
        "Ты — психолог, мастер анализа снов. Интерпретируй сны пользователя через призму психологии (Фрейд, Юнг), "
        "выявляя эмоции, страхи, желания или конфликты. Избегай общих фраз и дай один чёткий вывод о том, "
        "что эти сны отражают в психике пользователя. Не анализируй каждый сон отдельно, а суммируй их в целостный вывод."
    )
    
    if user_description:
        base_prompt += f"\n\nОписание пользователя: {user_description}"
    
    return base_prompt


def get_esoteric_prompt(user_description: str | None = None) -> str:
    """
    Промпт для эзотерического анализа (сонники, таро)
    """
    base_prompt = (
        "Ты — эзотерик, знаток мистических традиций. Анализируй сны пользователя через символы и знаки, опираясь на сонники, "
        "астрологию и таро. Избегай общих фраз и дай один ясный вывод о том, что эти сны предвещают или раскрывают. "
        "Не разбирай каждый сон отдельно, а объедини их в единое толкование."
    )
    
    if user_description:
        base_prompt += f"\n\nОписание пользователя: {user_description}"
    
    return base_prompt


def get_prompt_by_role(role: str, user_description: str | None = None) -> str:
    """
    Получить промпт по роли
    
    Args:
        role: 'psychological' или 'esoteric'
        user_description: Описание пользователя (опционально)
    
    Returns:
        Системный промпт для LLM
    """
    if role == "psychological":
        return get_psychological_prompt(user_description)
    elif role == "esoteric":
        return get_esoteric_prompt(user_description)
    else:
        raise ValueError(f"Unknown role: {role}")


def get_temperature_by_role(role: str) -> float:
    """
    Получить temperature для LLM по роли
    
    Args:
        role: 'psychological' или 'esoteric'
    
    Returns:
        Temperature value (0.0 - 1.0)
    """
    if role == "psychological":
        return 0.3  # Более консервативный анализ
    elif role == "esoteric":
        return 0.7  # Более творческий анализ
    else:
        return 0.5  # Дефолтное значение

