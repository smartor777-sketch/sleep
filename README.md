# JungAI - AI-powered Dream Journal

**JungAI** — мобильное приложение для записи и анализа снов с помощью AI в юнгианском стиле.

## Особенности

- **Без регистрации:** анонимная авторизация по `device_id`, опциональная привязка Google/Apple
- **Запись снов:** чат-лента с текстовым и голосовым вводом (speech-to-text)
- **AI-анализ:** диалоговый чат по каждому сну — первичный анализ + follow-up вопросы
- **Поиск и календарь:** быстрый поиск по снам, фильтрация по дате
- **Профиль и статистика:** streak, total dreams, распределение по дням недели

## Архитектура

```
┌─────────────┐      ┌─────────────┐      ┌──────────────────┐
│   Flutter    │─────>│   Backend   │─────>│   LLM Service    │
│   Client     │      │  (FastAPI)  │      │ (Gonka Proxy /   │
│ iOS/Android  │      │             │      │  OpenAI-compat)  │
└─────────────┘      └─────────────┘      └──────────────────┘
                           │
                ┌──────────┼──────────┐
                │          │          │
           ┌────▼───┐ ┌───▼────┐ ┌──▼────┐
           │Postgres│ │ Redis  │ │ MinIO │
           └────────┘ └────────┘ └───────┘
                │
           ┌────▼───────┐
           │   Celery   │
           │   Worker   │
           └────────────┘
```

## Технологический стек

### Backend
- **FastAPI** — асинхронный веб-фреймворк
- **SQLAlchemy 2.0** (async) — ORM
- **PostgreSQL** — база данных
- **Redis** — брокер сообщений для Celery
- **Celery** — фоновые задачи (анализ снов, follow-up ответы)
- **MinIO** — S3-совместимое хранилище
- **JWT** — аутентификация

### LLM Service
- **Gonka Proxy** — OpenAI-совместимый API (модель Qwen3-235B)
- **FastAPI** — REST-обёртка

### Client
- **Flutter** — iOS / Android
- **Provider** — state management
- **flutter_secure_storage** — хранение токенов
- **speech_to_text** — голосовой ввод
- **flutter_markdown** — рендеринг Markdown-ответов LLM

### DevOps
- **Docker + Docker Compose** — контейнеризация

## Установка и запуск

### Требования
- Docker и Docker Compose
- Gonka Proxy API key (или YandexGPT credentials)
- Flutter SDK (для клиента)

### Настройка переменных окружения

Создайте файл `.env` в корне проекта:

```env
# Database
POSTGRES_USER=jungai
POSTGRES_PASSWORD=your_secure_password
POSTGRES_DB=jungai_db

# JWT
JWT_SECRET_KEY=your-very-secret-key-change-in-production

# LLM (Gonka Proxy)
GONKA_API_KEY=sk-your-api-key
GONKA_MODEL=Qwen/Qwen3-235B-A22B-Instruct-2507-FP8

# MinIO
MINIO_ROOT_USER=minioadmin
MINIO_ROOT_PASSWORD=minioadmin

# Email (SMTP) - опционально
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password
SMTP_FROM=noreply@jungai.app

# OAuth2 (опционально)
GOOGLE_CLIENT_ID=your_google_client_id
APPLE_CLIENT_ID=your_apple_client_id
```

### Запуск сервисов

```bash
docker-compose up --build
```

Это запустит:
- **Backend API** на `http://localhost:8000`
- **LLM Service** на `http://localhost:8001`
- **PostgreSQL** на `localhost:5432`
- **Redis** на `localhost:6379`
- **MinIO** на `http://localhost:9000` (Console: `http://localhost:9001`)
- **Celery Worker**

### Запуск Flutter-клиента

```bash
cd client
flutter pub get
flutter run
```

### Проверка работоспособности

```bash
curl http://localhost:8000/health
curl http://localhost:8001/health
```

## API

Интерактивная документация после запуска:
- **Swagger UI:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc

### Endpoints

| Группа | Метод | Путь | Назначение |
|--------|-------|------|-----------|
| Auth | POST | `/api/v1/auth/anonymous` | Анонимный вход (device_id) |
| Auth | POST | `/api/v1/auth/link` | Привязка Google/Apple |
| Auth | POST | `/api/v1/auth/register` | Регистрация (email/password) |
| Auth | POST | `/api/v1/auth/login` | Вход |
| Auth | POST | `/api/v1/auth/refresh` | Обновление токена |
| Dreams | POST | `/api/v1/dreams` | Создать сон |
| Dreams | GET | `/api/v1/dreams` | Список снов (пагинация) |
| Dreams | GET | `/api/v1/dreams/search?q=` | Поиск |
| Dreams | PUT | `/api/v1/dreams/{id}` | Обновить |
| Dreams | DELETE | `/api/v1/dreams/{id}` | Удалить |
| Analysis | POST | `/api/v1/analyses` | Запросить анализ (async) |
| Analysis | GET | `/api/v1/analyses/dream/{id}` | Результат анализа |
| Analysis | GET | `/api/v1/analyses/task/{id}` | Статус задачи |
| Chat | POST | `/api/v1/messages` | Follow-up сообщение |
| Chat | GET | `/api/v1/messages/dream/{id}` | История чата |
| Chat | GET | `/api/v1/messages/task/{id}` | Статус ответа |
| Users | GET | `/api/v1/users/me` | Текущий пользователь |
| Users | PUT | `/api/v1/users/me` | Обновить профиль |
| Stats | GET | `/api/v1/stats/me` | Статистика |

## Разработка

### Локальный запуск (без Docker)

```bash
# Backend
cd backend
pip install -r requirements.txt
uvicorn main:app --reload

# LLM Service
cd llm_service
pip install -r requirements.txt
uvicorn main:app --reload --port 8001

# Celery Worker
cd backend
celery -A celery_app worker --loglevel=info
```

### Миграции БД

```bash
cd backend
alembic revision --autogenerate -m "описание"
alembic upgrade head
```

## Roadmap

- [x] Аутентификация (JWT, anonymous, OAuth2)
- [x] CRUD снов с лимитами
- [x] AI-анализ через Celery
- [x] Диалоговый чат по анализу (follow-up)
- [x] Flutter-клиент (чат-лента, анализ, профиль)
- [x] Поиск и календарь
- [x] Голосовой ввод (speech-to-text)
- [x] Markdown-рендеринг ответов LLM
- [x] Переход на Gonka Proxy (OpenAI-compatible)
- [ ] Экспорт в PDF/JSON
- [ ] WebSocket streaming ответов
- [ ] Мониторинг (Sentry)

## Контакты

- Telegram: [@okolo_boga](https://t.me/okolo_boga)
- GitHub: [okoloboga](https://github.com/okoloboga)

## Лицензия

[MIT License](LICENSE.md)
