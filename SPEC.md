# Техническое задание: Рефакторинг JungAI в Backend для мобильного приложения

## 1. Цель проекта

Создать современную, масштабируемую backend-платформу для мобильного приложения **JungAI** (iOS/Android), ориентированного на запись и анализ снов.

Цель — извлечь существующую бизнес-логику из монолитного Telegram-бота и построить универсальный backend, к которому в будущем можно подключить различные клиенты (мобильное приложение, веб-сайт, бот).

**Основной интерфейс:** Мобильные приложения (iOS/Android)

---

## 2. Этапы реализации

Проект реализуется в два этапа для минимизации рисков и ускорения получения рабочего продукта.

### **Этап 1: MVP Backend**

**Задача:** Получить работающий API с базовой функциональностью.

**Компоненты:**
- **FastAPI Backend**
- **LLM Service**
- **PostgreSQL**
- **Redis** (кэш + Celery broker)
- **Celery** (фоновые задачи)
- **S3/MinIO** (хранилище файлов)

**Технологии на этапе 1:**
- Python 3.11+, FastAPI, Uvicorn
- SQLAlchemy (async) для работы с БД
- Pydantic v2 для валидации данных
- JWT-аутентификация (access/refresh tokens)
- OAuth2 (Google, Apple Sign-In)
- Email verification + Password reset
- Celery + Redis для фоновых задач (LLM-анализ)
- S3-совместимое хранилище для изображений
- Docker + Docker Compose

### **Этап 2: Расширение функциональности**

**Задача:** Добавить продвинутые возможности, улучшить производительность и пользовательский опыт.

**Дополнительные фичи на этапе 2:**
- **Real-time streaming** ответов от LLM через WebSocket
- **Миграции базы данных** с помощью Alembic
- **Продвинутая безопасность:** rate-limiting, CORS policies
- **Мониторинг и логирование:** Sentry, structured logging
- **Поддержка дополнительных LLM-провайдеров** (OpenAI, Gemini)

---

## 3. Архитектура

```
sna_net/
│
├── backend/                     # FastAPI-бэкенд
│   ├── main.py                  # Точка входа (FastAPI app)
│   ├── database.py              # Подключение к PostgreSQL
│   ├── models/                  # ORM-модели (SQLAlchemy)
│   │   ├── user.py
│   │   ├── dream.py
│   │   ├── analysis.py
│   │   └── oauth.py
│   ├── schemas/                 # Pydantic-схемы
│   │   ├── user.py
│   │   ├── dream.py
│   │   ├── analysis.py
│   │   └── auth.py
│   ├── api/                     # Роуты
│   │   ├── auth.py              # Регистрация, логин, OAuth2
│   │   ├── dreams.py            # CRUD снов
│   │   ├── analyses.py          # Анализ снов
│   │   ├── search.py            # Поиск по снам
│   │   ├── export.py            # Экспорт в PDF/JSON
│   │   ├── voice.py             # Обработка голосовых сообщений
│   │   ├── admin.py             # Админ-эндпоинты
│   │   └── websocket.py         # (Этап 2) Streaming
│   ├── services/
│   │   ├── dream_service.py
│   │   ├── analysis_service.py
│   │   ├── auth_service.py
│   │   ├── email_service.py
│   │   ├── voice_service.py
│   │   ├── export_service.py
│   │   └── storage_service.py   # S3/MinIO интеграция
│   ├── llm_client.py            # HTTP-клиент для LLM Service
│   ├── celery_app.py            # Celery конфигурация
│   ├── tasks.py                 # Celery задачи
│   ├── config.py                # Настройки через pydantic-settings
│   ├── dependencies.py          # FastAPI dependencies (JWT, DB)
│   ├── .env.example
│   └── Dockerfile
│
├── llm_service/                 # Микросервис для LLM
│   ├── main.py                  # FastAPI для генерации
│   ├── providers/
│   │   ├── yandex.py            # YandexGPT
│   │   ├── openai.py            # (Этап 2)
│   │   └── gemini.py            # (Этап 2)
│   ├── prompts.py               # Шаблоны промптов
│   ├── config.py
│   └── Dockerfile
│
├── docker-compose.yml           # Запуск всех сервисов
├── .gitignore
└── README.md                    # Обновлённый README
```

---

## 4. Компоненты системы

### 4.1. FastAPI Backend
**Назначение:** Ядро бизнес-логики, API для мобильного приложения, управление данными.

**Функции (Этап 1):**
- **Аутентификация:**
  - Регистрация (email + password)
  - Логин (JWT: access + refresh tokens)
  - OAuth2 (Google, Apple Sign-In)
  - Email verification (подтверждение email)
  - Password reset (восстановление пароля)
  - Удаление аккаунта
  
- **Управление снами:**
  - Создание сна (текст или голосовое сообщение)
  - Получение списка снов (с пагинацией)
  - Получение сна по ID
  - Редактирование сна (title, content, emoji, comment, cover)
  - Удаление сна
  - Загрузка обложек (cover) в S3/MinIO
  
- **Анализ снов:**
  - Запрос анализа сна (асинхронная задача через Celery)
  - Получение статуса задачи
  - Получение результата анализа
  - Один сон = один анализ (запрет повторного анализа)
  
- **Поиск:**
  - Поиск по тексту снов (PostgreSQL full-text search)
  
- **Экспорт:**
  - Экспорт всех снов пользователя в PDF
  - Экспорт всех снов пользователя в JSON
  
- **Лимиты:**
  - Проверка лимита записи снов (5 снов/день по timezone пользователя)
  - Проверка возможности анализа (один анализ на сон)
  
- **Админ-эндпоинты:**
  - Статистика (пользователи, сны, анализы)
  - Управление пользователями (просмотр, блокировка)

**Функции (Этап 2):**
- Потоковая передача (streaming) ответов от нейросети через WebSocket
- Поддержка дополнительных LLM-провайдеров
- Rate-limiting на уровне API

---

### 4.2. LLM Service
**Назначение:** Изолированный сервис для генерации анализа снов с использованием LLM.

**Функции (Этап 1):**
- Приём запроса на анализ (текст сна, роль, user description)
- Формирование промпта на основе роли:
  - **psychological** (Фрейд, Юнг)
  - **esoteric** (сонники, таро)
- Вызов YandexGPT
- Возврат готового результата

**Функции (Этап 2):**
- Поддержка streaming-ответов
- Возможность подключения других LLM-провайдеров (OpenAI, Gemini)

---

### 4.3. База данных (PostgreSQL)

#### **Таблица: users**
```sql
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255),  -- nullable для OAuth2 пользователей
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    timezone VARCHAR(50) DEFAULT 'UTC',  -- для расчета лимитов по времени пользователя
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    email_verified BOOLEAN DEFAULT FALSE,
    is_active BOOLEAN DEFAULT TRUE,
    is_admin BOOLEAN DEFAULT FALSE,
    
    -- Подписка (для будущего, если понадобится)
    sub_type VARCHAR(16) DEFAULT 'free',  -- 'free', 'premium'
    sub_expires_at TIMESTAMP WITH TIME ZONE DEFAULT NULL,
    
    -- Настройки анализа
    gpt_role VARCHAR(20) DEFAULT 'psychological',  -- 'psychological', 'esoteric'
    self_description TEXT DEFAULT NULL  -- контекст для LLM
);

CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_created_at ON users(created_at);
```

#### **Таблица: oauth_accounts**
```sql
CREATE TABLE oauth_accounts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    provider VARCHAR(50) NOT NULL,  -- 'google', 'apple'
    provider_user_id VARCHAR(255) NOT NULL,
    access_token TEXT,
    refresh_token TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    UNIQUE(provider, provider_user_id)
);

CREATE INDEX idx_oauth_user_id ON oauth_accounts(user_id);
CREATE INDEX idx_oauth_provider ON oauth_accounts(provider, provider_user_id);
```

#### **Таблица: dreams**
```sql
CREATE TABLE dreams (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    title VARCHAR(100),
    content TEXT NOT NULL,
    emoji VARCHAR(10) DEFAULT '',
    comment VARCHAR(256) DEFAULT '',
    cover_url VARCHAR(512) DEFAULT '',  -- URL изображения в S3/MinIO
    recorded_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),  -- время записи сна
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_dreams_user_id ON dreams(user_id);
CREATE INDEX idx_dreams_recorded_at ON dreams(recorded_at);
CREATE INDEX idx_dreams_content_fts ON dreams USING gin(to_tsvector('russian', content));  -- полнотекстовый поиск
```

#### **Таблица: analyses**
```sql
CREATE TABLE analyses (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    dream_id UUID NOT NULL REFERENCES dreams(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    result TEXT NOT NULL,  -- текст анализа от LLM
    gpt_role VARCHAR(20) NOT NULL,  -- роль, которая использовалась
    status VARCHAR(20) DEFAULT 'pending',  -- 'pending', 'processing', 'completed', 'failed'
    celery_task_id VARCHAR(255),  -- ID задачи Celery
    error_message TEXT,  -- если произошла ошибка
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    completed_at TIMESTAMP WITH TIME ZONE DEFAULT NULL,
    
    UNIQUE(dream_id)  -- один сон = один анализ
);

CREATE INDEX idx_analyses_dream_id ON analyses(dream_id);
CREATE INDEX idx_analyses_user_id ON analyses(user_id);
CREATE INDEX idx_analyses_status ON analyses(status);
CREATE INDEX idx_analyses_task_id ON analyses(celery_task_id);
```

#### **Таблица: email_verifications**
```sql
CREATE TABLE email_verifications (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    token VARCHAR(255) UNIQUE NOT NULL,
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_email_verifications_token ON email_verifications(token);
CREATE INDEX idx_email_verifications_user_id ON email_verifications(user_id);
```

#### **Таблица: password_resets**
```sql
CREATE TABLE password_resets (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    token VARCHAR(255) UNIQUE NOT NULL,
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    used BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_password_resets_token ON password_resets(token);
CREATE INDEX idx_password_resets_user_id ON password_resets(user_id);
```

---

## 5. API Endpoints

### 5.1. Аутентификация (`/api/v1/auth`)

| Метод | Endpoint | Описание |
|-------|----------|----------|
| POST | `/auth/register` | Регистрация (email + password) |
| POST | `/auth/login` | Логин (возврат access + refresh tokens) |
| POST | `/auth/refresh` | Обновление access token |
| POST | `/auth/logout` | Выход (инвалидация refresh token) |
| GET | `/auth/verify-email?token=...` | Подтверждение email |
| POST | `/auth/resend-verification` | Повторная отправка письма |
| POST | `/auth/forgot-password` | Запрос восстановления пароля |
| POST | `/auth/reset-password` | Сброс пароля с токеном |
| GET | `/auth/oauth/{provider}` | OAuth2 redirect (Google/Apple) |
| GET | `/auth/oauth/{provider}/callback` | OAuth2 callback |
| DELETE | `/auth/account` | Удаление аккаунта |

### 5.2. Управление снами (`/api/v1/dreams`)

| Метод | Endpoint | Описание |
|-------|----------|----------|
| POST | `/dreams` | Создать сон (текст) |
| POST | `/dreams/voice` | Создать сон из голосового сообщения |
| GET | `/dreams` | Список снов (пагинация) |
| GET | `/dreams/{dream_id}` | Получить сон по ID |
| PUT | `/dreams/{dream_id}` | Обновить сон |
| DELETE | `/dreams/{dream_id}` | Удалить сон |
| POST | `/dreams/{dream_id}/cover` | Загрузить обложку (multipart/form-data) |
| GET | `/dreams/search?q=...` | Поиск по снам |

### 5.3. Анализ снов (`/api/v1/analyses`)

| Метод | Endpoint | Описание |
|-------|----------|----------|
| POST | `/analyses` | Запросить анализ сна (async, возврат task_id) |
| GET | `/analyses/task/{task_id}` | Получить статус задачи |
| GET | `/analyses/dream/{dream_id}` | Получить анализ сна |
| GET | `/analyses` | Список всех анализов пользователя |

### 5.4. Экспорт (`/api/v1/export`)

| Метод | Endpoint | Описание |
|-------|----------|----------|
| GET | `/export/pdf` | Экспорт всех снов в PDF |
| GET | `/export/json` | Экспорт всех снов в JSON |

### 5.5. Пользователь (`/api/v1/user`)

| Метод | Endpoint | Описание |
|-------|----------|----------|
| GET | `/user/me` | Получить текущего пользователя |
| PUT | `/user/me` | Обновить профиль |
| PUT | `/user/settings` | Обновить настройки (gpt_role, self_description, timezone) |

### 5.6. Админ (`/api/v1/admin`)

| Метод | Endpoint | Описание |
|-------|----------|----------|
| GET | `/admin/stats` | Общая статистика (пользователи, сны, анализы) |
| GET | `/admin/users` | Список пользователей |
| GET | `/admin/users/{user_id}` | Информация о пользователе |
| PUT | `/admin/users/{user_id}/block` | Заблокировать пользователя |
| PUT | `/admin/users/{user_id}/unblock` | Разблокировать пользователя |

---

## 6. Бизнес-логика и ограничения

### 6.1. Лимиты
- **Запись снов:** 5 снов в день (расчет по timezone пользователя)
- **Анализ снов:** 1 анализ на сон (повторный анализ невозможен)
- Проверка лимитов происходит на уровне API перед выполнением операции

### 6.2. Роли LLM
- **psychological:** Анализ через призму психологии (Фрейд, Юнг), temperature=0.3
- **esoteric:** Анализ через символы и знаки (сонники, таро), temperature=0.7

### 6.3. Голосовые сообщения
- Клиент отправляет аудиофайл (multipart/form-data)
- Backend распознает речь через Google Speech-to-Text API
- Создается сон с распознанным текстом

### 6.4. Обложки снов
- Клиент загружает изображение (JPEG, PNG, до 5MB)
- Backend сохраняет в S3/MinIO
- В БД сохраняется URL изображения

### 6.5. Экспорт данных
- **PDF:** Все сны пользователя в красиво оформленном PDF (использовать ReportLab или WeasyPrint)
- **JSON:** Структурированный JSON со всеми данными (сны + анализы)

---

## 7. Celery Tasks (Фоновые задачи)

### 7.1. Анализ сна (`tasks.analyze_dream`)
```python
@celery_app.task(bind=True)
def analyze_dream(self, dream_id: str, user_id: str):
    """
    1. Получить сон из БД
    2. Получить настройки пользователя (gpt_role, self_description)
    3. Отправить запрос в llm_service
    4. Сохранить результат в таблицу analyses
    5. Обновить статус задачи
    """
```

### 7.2. Отправка email (`tasks.send_email`)
```python
@celery_app.task
def send_email(to: str, subject: str, body: str):
    """
    Отправка email через SMTP
    - Email verification
    - Password reset
    """
```

---

## 8. Технологический стек

### Backend
- **Framework:** FastAPI 0.110+
- **ASGI Server:** Uvicorn
- **ORM:** SQLAlchemy 2.0 (async)
- **DB Driver:** asyncpg
- **Validation:** Pydantic v2
- **JWT:** python-jose, passlib, bcrypt
- **OAuth2:** authlib
- **Task Queue:** Celery 5.3+
- **Cache/Broker:** Redis 7+
- **Storage:** boto3 (S3), minio (MinIO)
- **Speech-to-Text:** google-cloud-speech / SpeechRecognition
- **Export:** ReportLab / WeasyPrint (PDF), built-in json

### LLM Service
- **Framework:** FastAPI
- **LLM SDK:** yandex-cloud-ml-sdk

### Database
- **PostgreSQL:** 15+
- **Redis:** 7+

### DevOps
- **Containerization:** Docker, Docker Compose
- **Environment:** python-dotenv, pydantic-settings

---

## 9. План действий (MVP - Этап 1)

### Шаг 1: Подготовка инфраструктуры
1. Создать структуру каталогов `backend/` и `llm_service/`
2. Настроить `docker-compose.yml` (PostgreSQL, Redis, backend, llm_service)
3. Создать `.env` файлы для конфигурации

### Шаг 2: LLM Service
1. Реализовать FastAPI приложение
2. Перенести логику вызова YandexGPT из `utils/services.py`
3. Создать эндпоинт `POST /analyze` с параметрами:
   - `dream_text`: str
   - `gpt_role`: str
   - `user_description`: str | None
4. Реализовать формирование промптов
5. Протестировать с реальными данными

### Шаг 3: Backend - Database
1. Создать модели SQLAlchemy (`models/`)
2. Создать Pydantic схемы (`schemas/`)
3. Настроить async подключение к PostgreSQL
4. Создать таблицы через SQLAlchemy (позже перейти на Alembic)

### Шаг 4: Backend - Аутентификация
1. Реализовать регистрацию (email + password)
2. Реализовать логин (JWT: access + refresh tokens)
3. Реализовать email verification (отправка письма, подтверждение по токену)
4. Реализовать password reset
5. Интегрировать OAuth2 (Google, Apple)
6. Реализовать удаление аккаунта

### Шаг 5: Backend - CRUD снов
1. Перенести логику из `utils/db.py` в `services/dream_service.py`
2. Реализовать эндпоинты для управления снами
3. Интегрировать S3/MinIO для загрузки обложек
4. Реализовать проверку лимитов (5 снов/день)

### Шаг 6: Backend - Анализ снов
1. Настроить Celery + Redis
2. Создать задачу `analyze_dream` в `tasks.py`
3. Реализовать эндпоинт `POST /analyses` (создание задачи)
4. Реализовать эндпоинт `GET /analyses/task/{task_id}` (статус задачи)
5. Реализовать эндпоинт `GET /analyses/dream/{dream_id}` (результат анализа)
6. Реализовать проверку: один сон = один анализ

### Шаг 7: Backend - Дополнительные функции
1. Реализовать распознавание голосовых сообщений (`services/voice_service.py`)
2. Реализовать поиск по снам (PostgreSQL full-text search)
3. Реализовать экспорт в PDF
4. Реализовать экспорт в JSON

### Шаг 8: Backend - Админка
1. Реализовать эндпоинт статистики
2. Реализовать эндпоинты управления пользователями

### Шаг 9: Тестирование
1. Протестировать связку `backend ↔ llm_service`
2. Протестировать связку `backend ↔ Celery ↔ Redis`
3. Протестировать все эндпоинты (Postman/Insomnia)
4. Проверить лимиты и бизнес-логику

### Шаг 10: Документация
1. Обновить README.md
2. Добавить примеры запросов в API
3. Описать процесс деплоя

---

## 10. Этап 2: Расширение функциональности

После завершения MVP приступить к:
1. **WebSocket streaming** для real-time ответов от LLM
2. **Alembic миграции** для управления схемой БД
3. **Rate-limiting** на уровне API (slowapi)
4. **Мониторинг:** Sentry для отслеживания ошибок
5. **Поддержка дополнительных LLM:** OpenAI, Gemini
6. **Оптимизация производительности:** connection pooling, query optimization

---

## 11. Переменные окружения

### Backend `.env`
```bash
# Database
DATABASE_URL=postgresql+asyncpg://user:password@postgres:5432/jungai

# Redis
REDIS_URL=redis://redis:6379/0

# JWT
JWT_SECRET_KEY=your-secret-key
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30
JWT_REFRESH_TOKEN_EXPIRE_DAYS=7

# OAuth2
GOOGLE_CLIENT_ID=...
GOOGLE_CLIENT_SECRET=...
APPLE_CLIENT_ID=...
APPLE_TEAM_ID=...
APPLE_KEY_ID=...
APPLE_PRIVATE_KEY=...

# Email (SMTP)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password
SMTP_FROM=noreply@jungai.app

# S3/MinIO
S3_ENDPOINT=http://minio:9000
S3_ACCESS_KEY=minioadmin
S3_SECRET_KEY=minioadmin
S3_BUCKET=jungai-covers
S3_REGION=us-east-1

# LLM Service
LLM_SERVICE_URL=http://llm_service:8001

# Google Speech-to-Text
GOOGLE_APPLICATION_CREDENTIALS=/app/google-credentials.json
```

### LLM Service `.env`
```bash
# Yandex Cloud
YANDEX_FOLDER_ID=...
YANDEX_API_KEY=...
```

---

## 12. Модель монетизации

**Текущая модель:** Приложение покупается один раз (paid app в App Store / Google Play)

- Без внутренних подписок
- Без ограничений для купивших приложение
- Лимиты (5 снов/день, 1 анализ на сон) применяются ко всем пользователям

**Будущее (опционально):**
- Возможность добавить премиум-функции (больше анализов, дополнительные роли LLM)
- Поле `sub_type` и `sub_expires_at` оставлены для будущего расширения

---

## 13. Безопасность

### 13.1. Аутентификация
- Пароли хешируются с помощью bcrypt (минимум 12 раундов)
- JWT токены с коротким временем жизни (30 мин access, 7 дней refresh)
- Refresh tokens хранятся в Redis с TTL
- OAuth2 через проверенные библиотеки (authlib)

### 13.2. Валидация данных
- Все входящие данные валидируются через Pydantic
- Защита от SQL-инъекций (SQLAlchemy ORM)
- Ограничение размера загружаемых файлов (5MB для изображений, 10MB для аудио)

### 13.3. CORS
- Настроить CORS для мобильных приложений
- Ограничить разрешенные origins

### 13.4. GDPR Compliance
- Возможность удаления аккаунта (все данные удаляются каскадно)
- Экспорт всех данных пользователя (JSON)

---

## 14. Метрики успеха MVP

**Критерии готовности Этапа 1:**
- ✅ Пользователь может зарегистрироваться (email/password, OAuth2)
- ✅ Пользователь может записать сон (текст, голос)
- ✅ Пользователь может запросить анализ сна
- ✅ Анализ выполняется асинхронно (Celery)
- ✅ Пользователь может получить результат анализа
- ✅ Лимиты работают корректно (5 снов/день, 1 анализ на сон)
- ✅ Поиск по снам работает
- ✅ Экспорт в PDF/JSON работает
- ✅ Админ может получить статистику
- ✅ Все сервисы запускаются через `docker-compose up`

---

## 15. Дальнейшее развитие

После MVP возможные направления:
- **Мобильное приложение:** Разработка iOS/Android приложений
- **WebSocket streaming:** Real-time ответы от LLM
- **Дополнительные LLM:** OpenAI GPT-4, Google Gemini
- **Расширенная аналитика:** Графики эмоций, статистика снов
- **Социальные функции:** Шаринг снов (анонимно), комьюнити
- **Интеграция с носимыми устройствами:** Apple Watch, Fitbit
- **Напоминания:** Push-уведомления для записи снов

---

**Конец спецификации**
