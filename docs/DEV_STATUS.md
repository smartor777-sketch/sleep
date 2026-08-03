# InnerCore — статус разработки (dev-sleep-test)

Сервер: `sleep-test.kuban-forum.ru` → `2.26.51.8`
Репозиторий: `smartor777-sketch/sleep.git`, ветка `dev-sleep-test`

Последнее обновление: 2026-08-03

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
- **Деплой**: `/srv/sleep-test-web/frontend/dist/` (не `/srv/sleep-test/frontend/`).
- **Caddy**: `Cache-Control: no-cache` для `index.html` (кеш-бастинг).
- **Google GSI скрипт удалён** из `index.html` (источник «Готовлю ссылку...»).
- **Блок «Мобильное приложение»** удалён из `ProfilePage.tsx`.

### Тестовый пользователь
- `test.sleep@innercore.example.com` / `Test12345!`
- 4 сна: «Полёт над морем», «Лес и волк», «Запертая комната», «Разговор с бабушкой»
- Проанализирован 1 сон → карта строится (5 узлов).

## Коммиты (новые)

- `785b978` — email-only auth, SMTP (Yandex) sending, admin email-auth toggle.
- `7e68dd2` — email-mode toggle skips code step seamlessly (auth.py, AuthModal, api).
- `fa5a2f1` — remove mobile app section from profile, remove Google GSI script.
- `78a2ab8` — admin delete user with confirmation modal.

## Серверные заметки

- SSH: `plink -ssh -batch -pw "yO3aN0cU6efK" root@2.26.51.8 "…"`; upload — `pscp.exe -batch -pw …`.
- systemd: `innercore-backend`, `innercore-celery`, `innercore-llm` (конфиг `/srv/sleep-test/llm_service/.env`).
- PostgreSQL: `PGPASSWORD=inn3rc0re_dev_2026 psql -U innercore -h 127.0.0.1 -d innercore`.
- Caddy: `/etc/caddy/Caddyfile` (reverse proxy на :8000, статика из `/srv/sleep-test-web/frontend/dist/`).
- Backend restart: ~35 секунд, проверять по `journalctl -u innercore-backend` «Uvicorn running on http://127.0.0.1:8000».
- Админ: `admin@innercore.example.com` / `Admin12345!`.

## Next Move

1. Подключить соц-авторизацию (Google, Яндекс, VK, Telegram) — см. `SOCIAL_AUTH.md`.
2. При деплое фронта заливать 4 иконки + assets.
3. Запускать анализ остальных тестовых снов для насыщения карты.
