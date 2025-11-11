# JungAI - Backend API для анализа снов

**JungAI** — современная backend-платформа для мобильного приложения записи и анализа снов с использованием искусственного интеллекта.

## 🌟 Особенности

- **Регистрация и аутентификация:**
  - Email/Password с JWT токенами
  - OAuth2 (Google, Apple Sign-In)
  - Email verification
  - Password reset

- **Управление снами:**
  - Запись снов (текст или голосовое сообщение)
  - Редактирование и удаление
  - Загрузка обложек (изображения)
  - Поиск по снам
  - Лимиты: 5 снов в день

- **Анализ снов:**
  - AI-powered анализ через YandexGPT
  - Две роли: Психологический (Фрейд, Юнг) и Эзотерический (сонники, таро)
  - Асинхронная обработка через Celery
  - Один анализ на сон

- **Экспорт данных:**
  - Экспорт всех снов в PDF
  - Экспорт всех снов в JSON

## 🏗️ Архитектура

```
┌─────────────┐      ┌─────────────┐      ┌──────────────┐
│   Mobile    │─────▶│   Backend   │─────▶│ LLM Service  │
│     App     │      │  (FastAPI)  │      │ (YandexGPT)  │
└─────────────┘      └─────────────┘      └──────────────┘
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

## 🛠️ Технологический стек

### Backend
- **FastAPI** 0.110+ — современный асинхронный веб-фреймворк
- **SQLAlchemy 2.0** (async) — ORM для работы с БД
- **PostgreSQL 15** — реляционная база данных
- **Redis 7** — кэш и брокер сообщений для Celery
- **Celery 5.3** — фоновые задачи (анализ снов)
- **MinIO** — S3-совместимое хранилище для изображений
- **JWT** — аутентификация
- **Pydantic v2** — валидация данных

### LLM Service
- **YandexGPT** — генерация анализа снов
- **FastAPI** — REST API

### DevOps
- **Docker + Docker Compose** — контейнеризация

## 📦 Установка и запуск

### Требования
- Docker и Docker Compose
- YandexGPT API credentials (folder_id, api_key)

### Шаг 1: Клонирование репозитория
```bash
git clone https://github.com/your_username/sna_net.git
cd sna_net
```

### Шаг 2: Настройка переменных окружения

Создайте файл `.env` в корне проекта:

```env
# Database
POSTGRES_USER=jungai
POSTGRES_PASSWORD=your_secure_password
POSTGRES_DB=jungai_db

# JWT
JWT_SECRET_KEY=your-very-secret-key-change-in-production

# YandexGPT
YANDEX_FOLDER_ID=your_folder_id
YANDEX_API_KEY=your_api_key

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
GOOGLE_CLIENT_SECRET=your_google_client_secret
APPLE_CLIENT_ID=your_apple_client_id

# Logging
LOG_LEVEL=INFO
```

### Шаг 3: Запуск сервисов

```bash
# Переименовать новый docker-compose
mv docker-compose.yml docker-compose.old.yml
mv docker-compose.new.yml docker-compose.yml

# Запустить все сервисы
docker-compose up --build
```

Это запустит:
- **Backend API** на `http://localhost:8000`
- **LLM Service** на `http://localhost:8001`
- **PostgreSQL** на `localhost:5432`
- **Redis** на `localhost:6379`
- **MinIO** на `http://localhost:9000` (Console: `http://localhost:9001`)
- **Celery Worker** (фоновый процесс)

### Шаг 4: Проверка работоспособности

```bash
# Backend
curl http://localhost:8000/health

# LLM Service
curl http://localhost:8001/health
```

## 📚 API Документация

После запуска backend доступна интерактивная документация:

- **Swagger UI:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc

## 🔐 API Endpoints

### Аутентификация (`/api/v1/auth`)
- `POST /auth/register` — Регистрация
- `POST /auth/login` — Вход
- `POST /auth/refresh` — Обновление токена
- `GET /auth/verify-email` — Подтверждение email
- `POST /auth/forgot-password` — Запрос восстановления пароля
- `POST /auth/reset-password` — Сброс пароля
- `DELETE /auth/account` — Удаление аккаунта

### Сны (`/api/v1/dreams`)
- `POST /dreams` — Создать сон
- `GET /dreams` — Список снов (пагинация)
- `GET /dreams/{dream_id}` — Получить сон
- `PUT /dreams/{dream_id}` — Обновить сон
- `DELETE /dreams/{dream_id}` — Удалить сон
- `POST /dreams/{dream_id}/cover` — Загрузить обложку
- `GET /dreams/search?q=...` — Поиск снов

### Анализ (`/api/v1/analyses`)
- `POST /analyses` — Запросить анализ (async)
- `GET /analyses/task/{task_id}` — Статус задачи
- `GET /analyses/dream/{dream_id}` — Анализ по ID сна
- `GET /analyses` — Список всех анализов

## 💡 Примеры использования

### Регистрация
```bash
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "securepassword123",
    "first_name": "John"
  }'
```

### Создание сна
```bash
curl -X POST http://localhost:8000/api/v1/dreams \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "content": "Я летал над городом и встретил говорящего кота...",
    "title": "Полёт над городом",
    "emoji": "✈️"
  }'
```

### Запрос анализа
```bash
curl -X POST http://localhost:8000/api/v1/analyses \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "dream_id": "your-dream-uuid"
  }'
```

### Проверка статуса анализа
```bash
curl http://localhost:8000/api/v1/analyses/task/TASK_ID \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

## 🔧 Разработка

### Локальный запуск (без Docker)

#### Backend:
```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# Создать .env файл с настройками
cp .env.example .env

# Запустить
uvicorn main:app --reload
```

#### LLM Service:
```bash
cd llm_service
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Создать .env файл
cp .env.example .env

# Запустить
uvicorn main:app --reload --port 8001
```

#### Celery Worker:
```bash
cd backend
celery -A celery_app worker --loglevel=info
```

### Миграции БД (Alembic)

```bash
cd backend

# Создать миграцию
alembic revision --autogenerate -m "описание изменений"

# Применить миграции
alembic upgrade head

# Откатить миграцию
alembic downgrade -1
```

## 📊 Мониторинг

### MinIO Console
- URL: http://localhost:9001
- Login: `minioadmin` / `minioadmin`

### Celery Flower (опционально)
```bash
celery -A celery_app flower
```
URL: http://localhost:5555

## 🧪 Тестирование

```bash
cd backend
pytest
```

## 📝 Лицензия

[MIT License](LICENSE.md)

## 🤝 Контрибьюция

Мы открыты для контрибуций! Создавайте issues и pull requests.

## 📧 Контакты

- Telegram: [@okolo_boga](https://t.me/okolo_boga)
- GitHub: [okoloboga](https://github.com/okoloboga)

## 🙏 Благодарности

- [FastAPI](https://fastapi.tiangolo.com/)
- [SQLAlchemy](https://www.sqlalchemy.org/)
- [Celery](https://docs.celeryq.dev/)
- [YandexGPT](https://cloud.yandex.ru/services/yandexgpt)

---

**Примечание:** Этот проект находится в активной разработке. Функции голосовых сообщений, экспорта и админки будут добавлены в ближайшее время.

## 🚀 Roadmap

- [x] Аутентификация (JWT, OAuth2)
- [x] CRUD снов
- [x] Анализ снов через Celery
- [x] Загрузка обложек (S3/MinIO)
- [x] Поиск по снам
- [ ] Голосовые сообщения (speech-to-text)
- [ ] Экспорт в PDF/JSON
- [ ] Админка
- [ ] WebSocket для real-time streaming ответов
- [ ] Поддержка дополнительных LLM (OpenAI, Gemini)
- [ ] Rate limiting
- [ ] Мониторинг (Sentry, Prometheus)

