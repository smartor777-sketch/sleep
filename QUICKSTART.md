# 🚀 Быстрый старт JungAI Backend

## Минимальная настройка для запуска MVP

### 1. Клонировать репозиторий
```bash
git clone https://github.com/your_username/sna_net.git
cd sna_net
```

### 2. Создать файл .env

Создайте файл `.env` в корне проекта с минимальной конфигурацией:

```env
# Database
POSTGRES_USER=jungai
POSTGRES_PASSWORD=jungai123
POSTGRES_DB=jungai_db

# JWT Secret (смените в продакшене!)
JWT_SECRET_KEY=dev-secret-key-change-in-production

# YandexGPT (получите в https://cloud.yandex.ru/)
YANDEX_FOLDER_ID=ваш_folder_id
YANDEX_API_KEY=ваш_api_key

# MinIO
MINIO_ROOT_USER=minioadmin
MINIO_ROOT_PASSWORD=minioadmin
```

### 3. Переименовать docker-compose

```bash
mv docker-compose.yml docker-compose.old.yml
mv docker-compose.new.yml docker-compose.yml
```

### 4. Запустить

```bash
docker-compose up --build
```

Дождитесь сообщения:
```
jungai_backend    | INFO:     Application startup complete.
```

### 5. Проверить работоспособность

```bash
# Backend
curl http://localhost:8000/health

# LLM Service
curl http://localhost:8001/health
```

### 6. Открыть API документацию

Перейдите в браузере: **http://localhost:8000/docs**

---

## 🎯 Первые шаги с API

### 1. Зарегистрировать пользователя

```bash
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "password123",
    "first_name": "Test"
  }'
```

Ответ:
```json
{
  "access_token": "eyJhbGc...",
  "refresh_token": "eyJhbGc...",
  "token_type": "bearer"
}
```

Сохраните `access_token` для дальнейших запросов.

### 2. Создать сон

```bash
curl -X POST http://localhost:8000/api/v1/dreams \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "content": "Я летал над морем и видел дельфинов, которые пели песни",
    "title": "Полет над морем",
    "emoji": "🌊"
  }'
```

### 3. Запросить анализ сна

```bash
# Используйте dream_id из предыдущего ответа
curl -X POST http://localhost:8000/api/v1/analyses \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "dream_id": "YOUR_DREAM_UUID"
  }'
```

Ответ:
```json
{
  "analysis_id": "...",
  "task_id": "abc123...",
  "status": "pending",
  "message": "Analysis task created. Use task_id to check status."
}
```

### 4. Проверить статус анализа

```bash
curl http://localhost:8000/api/v1/analyses/task/TASK_ID \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

Когда `status` будет `SUCCESS`, результат появится в поле `result`.

### 5. Получить результат анализа

```bash
curl http://localhost:8000/api/v1/analyses/dream/DREAM_UUID \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

---

## 🔍 Полезные команды

### Просмотр логов

```bash
# Все сервисы
docker-compose logs -f

# Только backend
docker-compose logs -f backend

# Только Celery worker
docker-compose logs -f celery_worker
```

### Остановка сервисов

```bash
docker-compose down
```

### Полная очистка (включая volumes)

```bash
docker-compose down -v
```

### Перезапуск отдельного сервиса

```bash
docker-compose restart backend
```

---

## 🐛 Устранение неполадок

### Backend не запускается

1. Проверьте, что PostgreSQL готов:
```bash
docker-compose logs postgres
```

2. Проверьте переменные окружения в `.env`

### LLM Service возвращает ошибки

Проверьте правильность `YANDEX_FOLDER_ID` и `YANDEX_API_KEY`:
```bash
docker-compose logs llm_service
```

### Celery не обрабатывает задачи

```bash
docker-compose logs celery_worker
```

Убедитесь, что Redis работает:
```bash
docker-compose ps redis
```

---

## 📚 Что дальше?

- Изучите полную документацию API: http://localhost:8000/docs
- Прочитайте [README.md](README.new.md) для детальной информации
- Ознакомьтесь с [SPEC.md](SPEC.md) для понимания архитектуры

---

## 💡 Советы

1. **Email verification не работает без SMTP настроек** — пользователи могут работать без подтверждения email в dev режиме
2. **OAuth2 опционален** — можно работать без Google/Apple Sign-In
3. **MinIO Console** доступен на http://localhost:9001 (minioadmin/minioadmin)
4. **Поиск снов** работает по содержимому, заголовку и комментарию
5. **Лимит снов** по умолчанию 5 в день (можно изменить в `.env` → `DREAMS_PER_DAY_LIMIT`)

---

Готово! 🎉 Теперь у вас работает полнофункциональный backend для JungAI.

