Вот полноценный документ для интеграции.

⸻

PROXY_GONKA.md

Интеграция Gonka Proxy (OpenAI-compatible API)

⸻

1. Обзор

Gonka Proxy — это OpenAI-совместимый REST API, предоставляющий доступ к LLM через децентрализованную inference-сеть Gonka.

API полностью совместим с протоколом OpenAI Chat Completions и может использоваться как drop-in замена OpenAI при указании собственного base_url.

⸻

2. Базовая информация

Base URL

https://proxy.gonka.gg/v1

Аутентификация

Все прокси-эндпоинты требуют API-ключ.

Заголовок:

Authorization: Bearer sk-xxxxxxxxxxxxxxxx

Новые аккаунты получают 1,000,000 бесплатных токенов.

⸻

3. Основные эндпоинты

Метод	Путь	Авторизация	Назначение
GET	/health	Нет	Проверка работоспособности
GET	/models	Нет	Список доступных моделей
POST	/chat/completions	API Key	Генерация ответа модели
GET	/api/usage	JWT	Логи использования
GET	/api/usage/summary	JWT	Агрегированная статистика

Для интеграции чат-бота используется только:

POST /chat/completions


⸻

4. Модели

Модель передаётся строкой в поле "model".

Пример модели:

Qwen/Qwen3-235B-A22B-Instruct-2507-FP8

Для получения списка доступных моделей:

GET https://proxy.gonka.gg/v1/models

Ответ возвращает список моделей в формате OpenAI.

⸻

5. Формат запроса (Chat Completions)

Endpoint

POST https://proxy.gonka.gg/v1/chat/completions

Заголовки

Content-Type: application/json
Authorization: Bearer sk-...

Минимальный запрос

{
  "model": "Qwen/Qwen3-235B-A22B-Instruct-2507-FP8",
  "messages": [
    {
      "role": "user",
      "content": "Hello!"
    }
  ]
}


⸻

6. Структура messages

Массив messages полностью соответствует OpenAI Chat API.

Поддерживаемые роли:
	•	system
	•	user
	•	assistant
	•	tool

Пример диалога:

{
  "model": "Qwen/Qwen3-235B-A22B-Instruct-2507-FP8",
  "messages": [
    {
      "role": "system",
      "content": "You are a helpful AI assistant."
    },
    {
      "role": "user",
      "content": "Explain how blockchain works."
    }
  ]
}


⸻

7. Основные параметры генерации

Поддерживаются стандартные параметры OpenAI:

Параметр	Тип	Описание
temperature	number	Контроль креативности
top_p	number	Nucleus sampling
max_tokens	number	Максимум токенов в ответе
stream	boolean	Включение стриминга
tools	array	Tool / function calling

Пример с параметрами:

{
  "model": "Qwen/Qwen3-235B-A22B-Instruct-2507-FP8",
  "messages": [
    { "role": "user", "content": "Write a short poem." }
  ],
  "temperature": 0.7,
  "max_tokens": 200
}


⸻

8. Streaming Mode

Для потоковой генерации:

{
  "model": "Qwen/Qwen3-235B-A22B-Instruct-2507-FP8",
  "messages": [
    { "role": "user", "content": "Tell me a story." }
  ],
  "stream": true
}

Ответ возвращается в формате OpenAI streaming (Server-Sent Events).

Подходит для:
	•	чат-интерфейсов
	•	live-typing UX
	•	websocket/SSE проксирования

⸻

9. Tool / Function Calling

Proxy поддерживает OpenAI tool calling.

Если upstream модель не поддерживает tools нативно, proxy может эмулировать их через structured prompting (при включённой конфигурации).

Пример запроса

{
  "model": "Qwen/Qwen3-235B-A22B-Instruct-2507-FP8",
  "messages": [
    { "role": "user", "content": "What's the weather in Berlin?" }
  ],
  "tools": [
    {
      "type": "function",
      "function": {
        "name": "get_weather",
        "description": "Get current weather for a location",
        "parameters": {
          "type": "object",
          "properties": {
            "location": { "type": "string" }
          },
          "required": ["location"]
        }
      }
    }
  ]
}

Модель вернёт:

{
  "choices": [
    {
      "message": {
        "tool_calls": [
          {
            "id": "...",
            "type": "function",
            "function": {
              "name": "get_weather",
              "arguments": "{\"location\":\"Berlin\"}"
            }
          }
        ]
      }
    }
  ]
}


⸻

10. Формат ответа

Ответ полностью совместим с OpenAI Chat Completions:

{
  "id": "chatcmpl-...",
  "object": "chat.completion",
  "created": 1700000000,
  "model": "Qwen/Qwen3-235B-A22B-Instruct-2507-FP8",
  "choices": [
    {
      "index": 0,
      "message": {
        "role": "assistant",
        "content": "Hello! How can I help you today?"
      },
      "finish_reason": "stop"
    }
  ],
  "usage": {
    "prompt_tokens": 12,
    "completion_tokens": 18,
    "total_tokens": 30
  }
}


⸻

11. Ценообразование
	•	$0.00123 за 1,000,000 токенов
	•	Одинаковая ставка для prompt и completion
	•	Баланс списывается автоматически
	•	Новые аккаунты получают 1M токенов бесплатно

⸻

12. Rate Limits

На уровне proxy ограничения отсутствуют.
Балансировка нагрузки осуществляется через децентрализованную сеть Gonka.

⸻

13. Рекомендованная архитектура интеграции

Для backend-сервиса:
	1.	Хранить API ключ в переменной окружения.
	2.	Создать сервис-слой LLM (LLM Gateway).
	3.	Передавать историю диалога полностью в messages.
	4.	Логировать usage.total_tokens.
	5.	Реализовать retry при сетевых ошибках.
	6.	Ограничивать max_tokens для контроля стоимости.

⸻

14. Проверка работоспособности

Health-check:

GET https://proxy.gonka.gg/health

Проверка моделей:

GET https://proxy.gonka.gg/v1/models


⸻

15. Минимальный чек-лист интеграции
	•	Получен API ключ
	•	Настроен base_url
	•	Реализован POST /chat/completions
	•	Обработан формат choices[0].message.content
	•	Логируется usage
	•	Настроены таймауты и retry

⸻

16. Итог

Gonka Proxy полностью совместим с OpenAI Chat Completions API и может использоваться как прямая замена OpenAI при смене base_url.

Для базового чат-бота требуется:
	•	API ключ
	•	endpoint /chat/completions
	•	модель
	•	массив messages

Интеграция не требует дополнительных SDK или нестандартных протоколов.