# InnerCore — статус разработки (dev-sleep-test)

Прод-сервер: `sleep.kuban-forum.ru` → `87.120.186.100` (DE-LC-Production.play2go.cloud)
Репозиторий: `smartor777-sketch/sleep.git`, ветка `dev-sleep-test`

Последнее обновление: 2026-08-18

## Текущее состояние

### Авторизация: только email
- Соц-кнопки (Google, Яндекс, VK, Telegram) **удалены** с фронтенда.
- `AuthModal.tsx` — email-only: форма регистрации/входа + optional 6-значный код подтверждения.
- **Режим `email_auth_enabled`** (переключатель в админке):
  - **ON** (по умолчанию) — обычный режим: при регистрации required код с почты.
  - **OFF** — лёгкий режим (анти-спам): вход/регистрация без кода.
- Режим опрашивается через `GET /api/v1/auth/email-mode` (публичный эндпоинт).
- Фронт после регистрации проверяет режим: если OFF → сразу в аккаунт, если ON → шаг ввода кода.

### Email-рассылка: SMTP Яндекс
- Приоритет: **SmtpProvider** → Resend → Unisender → Brevo.
- SMTP Яндекс (`smtp.yandex.ru:465`, SSL) работает, письма приходят.
- Конфиг в `.env` на сервере: `SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASSWORD`, `SMTP_FROM`, `SMTP_USE_SSL`.

### Админ-панель (`/admin`)
- **Статистика**: юзеры, сны, анализы, анонимы, premium, актив за 7д.
- **Создание пользователей**: email + пароль + имя.
- **Управление пользователями**: поиск, сброс пароля, toggle admin/block.
- **Удаление пользователей**: кнопка «Удалить» с модальным окном предупреждения (данные удаляются каскадно).
- **Email-auth toggle**: включение/выключение режима кода.
- Нельзя удалить или заблокировать самого себя.

### Удаление пользователей (каскад)
- `DELETE /api/v1/admin/users/{user_id}` — эндпоинт + фронт.
- Каскад через SQLAlchemy: User → Dream → Analysis → DreamChunk → DreamSymbol → DreamSymbolEntity → DreamArchetype → AnalysisMessage → OAuthIdentity → Subscription → UserArchetype → EmailVerification → PasswordReset → UserMemoryDoc.
- Админ не может удалить сам себя (серверная проверка).

### Билинг и доступ (все — Pro)
- `billing_service.py` — `refresh_entitlements` форсирует `sub_type="pro"`, `sub_expires_at=None`.
- Trial-логика отключена, `has_full_access()` → `True` для всех.

### LLM: модель и fallback
- Основная модель: **`gemini-3.5-flash-lite`**.
- Gemini fallback-цепочка: `["gemini-3.6-flash", "gemini-3.5-flash"]`.
- Внешний fallback: **Mistral** (`mistral-large-latest`).

### Контекст чата LLM
- `CONTEXT_CHAR_BUDGET`: 400 000 символов (~100k токенов).
- `MAX_RECENT_MESSAGES`: 50.

### Карта снов
- Порог мержа: `_SYMBOL_MERGE_THRESHOLD = 0.80`.
- Семантические рёбра: `co_dream` + `embedding`.
- Кеш: `dream-map:v5`.

### Фронтенд
- **Сборка**: `tsc --noEmit && vite build` → `frontend/dist/`.
- **Деплой**: `/srv/sleep-prod/backend/frontend/dist/` (Caddy отдаёт как статику).
- **Caddy**: `Cache-Control: no-cache` для `index.html` (кеш-бастинг).
- **Google GSI скрипт удалён** из `index.html` (источник «Готовлю ссылку...»).
- **Блок «Мобильное приложение»** удалён из `ProfilePage.tsx`.

### Тестовый пользователь
- `test.sleep@innercore.example.com` / `Test12345!` (пароль сброшен 2026-08-18)
- 14 снов (10 добавлено 2026-08-18 для нагрузки), анализы строятся через celery.
- `sub_type=pro` (биллинг форсирует Pro для всех).

### Авто-анализ снов и уведомления (2026-08-18)
- **Авто-триггер**: `POST /api/v1/dreams` после сохранения сна сам ставит анализ в celery (статус ответа `analyzing`). Если enqueue не удалась (Redis/celery недоступны) — сон сохраняется со статусом `saved`, пользователь может запустить анализ вручную.
- **Очередь**: размер = число анализов в `pending`/`processing`; позиция сна в очереди отдаётся в `queue_position` (создание, деталь сна, trigger_analysis).
- **Уведомления пользователя**: таблица `notifications` (scope `user`). События: `analysis_started` (с позицией в очереди), `analysis_completed`, `analysis_failed`. API: `GET /api/v1/notifications`, `POST /notifications/{id}/read`, `POST /notifications/read-all`.
- **Админ-алерт очереди**: при размере очереди ≥ `analysis_queue_alert_threshold` (по умолчанию 10) — уведомление `scope=admin` в админ-панели + email админу (SMTP Яндекс, получатели из `ADMIN_EMAIL` + admins с подтверждённым email). Дедупликация через `app_settings.admin_queue_alert_active` (снимается, когда очередь падает ниже порога).
- **Админ-панель**: системные уведомления (`GET /api/v1/admin/notifications`, mark-read/read-all) + карточка «Очередь анализов» в статистике.
- **Фронтенд**: колокольчик уведомлений в Topbar (бейдж + дропдаун, поллинг 20с), глобальный поллер анализа (`GlobalAnalysisPoller`) обновляет статус сна на любой странице, на странице сна показывается позиция в очереди. Блок «Разбор InnerCore» постоянный: пока идёт анализ — индикатор «InnerCore погружается в сон…» + позиция в очереди, по завершении текст результата заменяет индикатор на месте (`63fdf48`).
- **Деплой на прод (2026-08-18)**: задеплоены `dc8067e` + `0d49de9` через `systemd-deploy.sh`; end-to-end проверен авто-анализ (сон → `analyzing` → уведомления `analysis_started`/`analysis_completed` → `completed`). `ADMIN_EMAIL=furi_wave@mail.ru` добавлен в `/srv/sleep-prod/backend/backend/.env`. ВАЖНО: prod-админ — `sleep@kuban-forum.ru` (не `admin@innercore.example.com`).

## Коммиты (новые)

- `785b978` — email-only auth, SMTP (Yandex) sending, admin email-auth toggle.
- `7e68dd2` — email-mode toggle skips code step seamlessly (auth.py, AuthModal, api).
- `fa5a2f1` — remove mobile app section from profile, remove Google GSI script.
- `78a2ab8` — admin delete user with confirmation modal.

## Серверные заметки

- SSH: `plink -ssh -batch -pw "<prod-password>" root@87.120.186.100 "…"`.
- systemd: `innercore-prod`, `celery-prod` (+ drop-in `--autoscale=2,1 --max-memory-per-child=300000`), `innercore-llm`.
- PostgreSQL: `PGPASSWORD=inn3rc0re_prod_2026 psql -U innercore -h 127.0.0.1 -d innercore`.
- Caddy: `/etc/caddy/Caddyfile` (reverse proxy :8000, статика из `/srv/sleep-prod/backend/frontend/dist/`).
- Деплой: `bash /srv/sleep-prod/backend/deploy/systemd-deploy.sh origin/dev-sleep-test` (pip install + **обязательный** рестарт сервисов).
- Backend restart: `systemctl restart innercore-prod`, проверять `journalctl -u innercore-prod` «Uvicorn running on http://127.0.0.1:8000».
- ⚠️ **SIGILL celery (инцидент 2026-08-18)**: воркер, стартовавший ДО пересборки C-расширений (`.so`), падает с SIGILL (`invalid opcode in immutabledict.so`), анализы зависают в pending. Лечится `systemctl restart celery-prod`. После любого pip install рестарт обязателен.
- Админ: `admin@innercore.example.com` / `Admin12345!`.

## Next Move

1. Подключить соц-авторизацию (Google, Яндекс, VK, Telegram) — см. `SOCIAL_AUTH.md`.
2. При деплое фронта заливать 4 иконки + assets.
3. ~~Авто-триггер анализа после создания сна~~ — сделано (см. «Авто-анализ снов и уведомления»).
