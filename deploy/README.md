# InnerCore — production deploy

**Реальный прод**: bare-metal systemd на `87.120.186.100` (DE-LC-Production.play2go.cloud), домен **`sleep.kuban-forum.ru`**. Docker-деплой ниже — legacy-путь для старой инфраструктуры (msk-1), НЕ используется.

## Актуальный прод (systemd, 87.120.186.100)

| Компонент | systemd-юнит | Порт | Путь |
|-----------|--------------|------|------|
| Backend (FastAPI) | `innercore-prod.service` | 8000 | `/srv/sleep-prod/backend/backend` |
| LLM-сервис (Gemini) | `innercore-llm.service` | 8001 | `/srv/sleep-prod/backend/llm_service` |
| Celery worker | `celery-prod.service` | — | venv backend, drop-in `celery-prod.service.d/memory.conf` |
| PostgreSQL 17 (native, systemd) | `postgresql@17-main.service` | 5432 | кластер Debian |
| Redis (native, systemd) | `redis-server.service` | 6379 | стандартный конфиг |
| Caddy (reverse proxy + TLS) | `caddy.service` | 80/443 | `/etc/caddy/Caddyfile` |

Caddy: `sleep.kuban-forum.ru` → `/api/*` → `127.0.0.1:8000`, статика — `/srv/sleep-prod/backend/frontend/dist`.

## Деплой (systemd)

Скрипт **`deploy/systemd-deploy.sh`** запускается на сервере от root:

```bash
bash /srv/sleep-prod/backend/deploy/systemd-deploy.sh origin/dev-sleep-test
```

Что делает:
1. `git fetch + checkout` нужного ref в `/srv/sleep-prod/backend`.
2. venv + `pip install` для `backend/` и `llm_service/`.
3. `npm ci && npm run build` фронтенда (dist).
4. `systemctl restart innercore-llm innercore-prod celery-prod` — **обязательно** после каждого pip install.
5. Health-check статуса юнитов и слушающих портов.

> ⚠️ Рестарт обязателен: pip может пересобрать C-расширения (SQLAlchemy Cython,
> pydantic_core и т.п.). Работающий процесс держит в памяти старые страницы `.so`;
> вызов нового кода падает с **SIGILL/SIGSEGV** (инцидент 2026-08-18: celery
> упал с `invalid opcode in immutabledict.so`, сны зависли в pending). Полный
> рестарт подхватывает свежие бинарники с диска.

### systemd-юниты

Копии фактических юнитов лежат в `deploy/systemd/`:

| Файл | Назначение |
|------|-----------|
| `systemd/innercore-prod.service` | uvicorn backend на :8000 |
| `systemd/innercore-llm.service` | uvicorn LLM на :8001 |
| `systemd/celery-prod.service` | celery worker |
| `systemd/celery-prod.service.d/memory.conf` | override: `--autoscale=2,1 --max-memory-per-child=300000` |

Установка:

```bash
cp deploy/systemd/*.service /etc/systemd/system/
mkdir -p /etc/systemd/system/celery-prod.service.d
cp deploy/systemd/celery-prod.service.d/memory.conf /etc/systemd/system/celery-prod.service.d/
systemctl daemon-reload
systemctl enable --now innercore-prod innercore-llm celery-prod
```

### .env

- Backend: `/srv/sleep-prod/backend/backend/.env`
- LLM: `/srv/sleep-prod/backend/llm_service/.env`
- Frontend: `/srv/sleep-prod/backend/frontend/.env` (`VITE_API_BASE_URL=https://sleep.kuban-forum.ru`, `VITE_APP_VERSION=0.4.2`)

Ключевые переменные backend: `DATABASE_URL=postgresql+asyncpg://innercore:...@127.0.0.1:5432/innercore`, `REDIS_URL=redis://127.0.0.1:6379/0`, `LLM_SERVICE_URL=http://127.0.0.1:8001`, `S3_ENDPOINT=http://127.0.0.1:9000`, `EMBEDDINGS_PROVIDER=gemini`.

## Операционные команды

```bash
# Статус
systemctl status innercore-prod innercore-llm celery-prod
# Логи backend
journalctl -u innercore-prod -f
# Логи celery (там падают SIGILL и задачи)
journalctl -u celery-prod -f
# Рестарт одного сервиса
systemctl restart celery-prod
# Celery: посмотреть очередь
redis-cli -n 0 llen celery
```

## Сборка фронтенда

```bash
cd /srv/sleep-prod/backend/frontend
cat > .env << 'EOF'
VITE_API_BASE_URL=https://sleep.kuban-forum.ru
VITE_APP_VERSION=0.4.2
VITE_GOOGLE_CLIENT_ID=
EOF
npm ci && npm run build
```

Готовый дистрибутив — `frontend/dist/` (Caddy отдаёт его как статику).

---

## Legacy: Docker-деплой (msk-1) — НЕ используется

Прошлая схема разворачивалась на `msk-1` (`5.42.100.202`) через Docker Compose
(`deploy/docker-compose.prod.yml`, `deploy/deploy.sh`, GHCR-образы
`ghcr.io/core-euler/sna_net-*`, CI — `.github/workflows/deploy.yml`). Текущий прод
на неё НЕ переведён: реальный сервер — 87.120.186.100, PostgreSQL/Redis native,
frontend собирается из исходников. Сохранено для истории/отката.
