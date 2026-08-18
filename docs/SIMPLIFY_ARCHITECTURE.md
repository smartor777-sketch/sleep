# Упрощение архитектуры backend (InnerCore / sleep-prod) для небольших нагрузок

Статус: предложение. Дата: 2026-08-11.

## 1. Текущее состояние

Backend InnerCore на prod-сервере (87.120.186.100, `sleep.kuban-forum.ru`) развёрнут так:

| Компонент | Как запущен | Заметки |
|---|---|---|
| FastAPI backend | systemd `innercore-prod.service` (venv, uvicorn) | основной API, порт 8000 |
| LLM-сервис | systemd `innercore-llm.service` (порт 8001) | прокси на Gemini |
| **Celery worker** | systemd `celery-prod.service` | `--autoscale=2,1 --max-memory-per-child=300000` → **2 процесса ≈ 615 МБ** |
| **Redis** | systemd `redis-server.service` (native) | broker+backend Celery, а также auth-токены |
| PostgreSQL | systemd `postgresql@17-main.service` (native, Debian cluster) | источник истины |
| MinIO | не запущен | S3-эндпоинт прописан в .env, но не используется |

Задачи Celery (`backend/tasks.py`):
- `analyze_dream_task` — долгий async LLM-вызов (до 10 мин), retry на `LLMTransientError`;
- `reply_to_dream_chat_task` — async LLM-чат;
- `send_email_task` — отправка письма.

Все три — по сути **async I/O** (HTTP к LLM/внешним API), а не CPU-работа. Celery синхронный, поэтому код гоняется через обёртку `_run_in_worker_loop()` (отдельный event loop на воркер).

## 2. Почему это избыточно при ~20 юзерах/день

Celery оправдан, когда нужны: большая параллельность, горизонтальное масштабирование, гарантированная доставка задач, распределённые воркеры, планировщик. При 20 юзерах/день воркеры почти всегда простаивают, а платим мы за это:

- ~615 МБ ОЗУ на 2 процесса воркеров;
- отдельный сервис + systemd-юнит + деплой;
- Redis как брокер очереди;
- обвязку async→sync (`_run_in_worker_loop`) и усложнённую отладку.

## 3. Целевая архитектура (для малой нагрузки)

- **Убрать Celery целиком.** Фоновые задачи выполняет `asyncio.create_task(...)` прямо в процессе FastAPI — код уже async, мост не нужен.
- **Статус/прогресс — в PostgreSQL** вместо `AsyncResult` из Redis. Достаточно полей `status`, `error`, `started_at`, `finished_at` у `Analysis`. Контракт эндпоинтов статуса сохраняется, меняется только источник данных.
- **Ретраи** — `tenacity` (или простой цикл) на `LLMTransientError`: backoff 2..120 c, до 4 попыток — прямая замена `autoretry_for`.
- **Email** — `fastapi.BackgroundTasks` (fire-and-forget после ответа).
- **Redis оставить** — он нужен для auth-токенов (см. ниже), но как лёгкий standalone, а не брокер.
- Один процесс, один деплой, один event loop.

> **Важно:** Redis используется не только Celery:
> - `services/telegram_auth_service.py` — short-lived токены Telegram-авторизации;
> - `services/yandex_auth_service.py` — state для Yandex OAuth;
> - `api/auth.py` — JWT под `auth_token`.
>
> Удаляется только Celery-часть, Redis остаётся как есть.

Эскиз:

```python
# services/background.py
async def _run_analysis_job(analysis_id: str):
    await db_update(Analysis, analysis_id, status="running")
    try:
        result = await llm_client.analyze_dream(analysis_id)  # с tenacity-ретраями
        await db_update(Analysis, analysis_id, status="done", result=result)
    except LLMTransientError as e:
        await db_update(Analysis, analysis_id, status="failed", error=str(e))

# api/analysis.py
@app.post("/analyses/{id}/run")
async def run_analysis(id: UUID):
    asyncio.create_task(_run_analysis_job(str(id)))
    return {"status": "started"}
```

## 4. План миграции

1. **Бэкап** (обязательный, см. раздел 6).
2. Добавить `services/background.py` (джоб-раннер + ретраи + запись статуса в БД).
3. Заменить вызовы `.delay()` / `.apply_async` в `services/analysis_service.py`, `services/message_task_service.py`.
4. Переписать `get_task_status` на чтение из БД (формат ответа не менять).
5. Выпилить `celery_app.py`, `tasks.py`, зависимость `celery` из `requirements.txt` (в git-истории остаются).
6. `systemctl disable --now celery-prod.service`.
7. Наблюдение ~1 неделя: память, ошибки, статусы задач.

Откат: runbook в разделе 6.

## 5. Что получаем

- **−~615 МБ ОЗУ** (2 celery-воркера) из ~1.8 ГБ занятых; Redis остаётся (он нужен и лёгкий).
- Один процесс backend; убраны брокер-зависимость и `_run_in_worker_loop`.
- Проще деплой, отладка и логирование — всё в одном приложении.
- Меньше контейнеров в `deploy/docker-compose.prod.yml`.

## 6. Бэкапы текущей инфраструктуры (для случая роста нагрузки)

Упрощение выгодно сейчас, но при росте нагрузки или новых требованиях (гарантированная доставка, периодика, горизонтальное масштабирование) очередь может снова понадобиться. Чтобы не собирать её заново, **до миграции** делаем полный страховочный комплект:

1. **Git-точка** `before-celery-removal` (ветка/тег) — весь код с `celery_app.py`, `tasks.py`, `services/*`, `entrypoint.sh`.
2. **Systemd-юниты** — копии `celery-prod.service`, `redis-server.service`, `innercore-prod.service` → `/srv/sleep-prod/backup/systemd/` и в репозиторий `deploy/systemd/` (уже добавлены).
3. **Redis** — `/etc/redis/redis.conf` + дамп (`SAVE`/`BGSAVE`); главное — настройки и пароль.
4. **`.env`** — зафиксировать `REDIS_URL` и все переменные celery-воркера (полный список в compose).
5. **`deploy/docker-compose.prod.yml`** — секции `celery_worker` и `celery_beat` **не удалять**, пометить `# fallback: поднять при росте нагрузки`. Это готовый план подъёма через GHCR-образы.
6. **PostgreSQL** — `pg_dump` базы (источник истины статусов/задач).
7. **Runbook отката** (ниже) — несколько команд, возвращающих Celery+Redis-путь.

**Runbook отката (подъём Celery обратно):**

```bash
# 1. Вернуть код
git checkout before-celery-removal
# 2. Вернуть юниты из бэкапа и запустить
cp /srv/sleep-prod/backup/systemd/celery-prod.service /etc/systemd/system/
systemctl daemon-reload && systemctl enable --now redis-server celery-prod.service
# 3. (опция) docker-путь
docker compose -f deploy/docker-compose.prod.yml up -d celery_worker celery_beat
# 4. Проверить
journalctl -u celery-prod.service -f
```

При росте нагрузки с готового бэкапа можно сразу поднять либо Celery как было, либо перейти на лёгкую замену (Dramatiq/arq) — конфиг и деплой уже задокументированы. Бэкап юнитов/конфигов обновлять при их изменении.

## 7. Триггеры для возврата очереди

- Стабильно больше ~5–10 одновременных фоновых задач (долгие LLM-сессии).
- Появилось требование гарантированной доставки (рестарт процесса не должен терять задачу).
- Горизонтальное масштабирование (2+ инстанса backend).
- Периодические задачи — вместо celery beat: `arq` / `Dramatiq` или `APScheduler`.

## 8. Открытые вопросы

- Приемлема ли потеря in-flight задач при рестарте процесса? (Для 20 юзеров/день — да, задача просто запускается заново.)
- Периодические задачи сейчас не используются (celery_beat в dev-compose закомментирован) — подтвердить для prod.
- Кто согласовывает и выполняет миграцию?
