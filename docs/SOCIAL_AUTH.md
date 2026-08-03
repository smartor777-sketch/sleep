# Подключение соц-авторизации (Google, Яндекс, VK, Telegram)

Руководство по восстановлению кнопок входа через соцсети на `sleep-test.kuban-forum.ru`.

Бэкенд уже готов — все эндпоинты и сервисы на месте. Нужно: настроить провайдеров, добавить env-переменные, восстановить UI-компоненты.

---

## Общая архитектура

```
Фронтенд → /auth/{provider}/init → Бэкенд → Редирект на провайдера
Провайдер → /auth/callback/{provider} → Бэкенд → JWT токены → Фронтенд
```

Все провайдеры используют **state-based polling** (кроме Google — через JS SDK):
1. Фронт запрашивает `GET /auth/{provider}/init` → получает `auth_url` + `state`.
2. Юзер переходит на `auth_url`, логинится, попадает на callback URL.
3. Бэкенд на callback обменивает code на token, находит/создаёт пользователя.
4. Фронт поллит `GET /auth/{provider}/status?state=...` → получает JWT токены.

---

## 1. Google

### Бэкенд: настройка Google Cloud Console

1. Перейти в [Google Cloud Console](https://console.cloud.google.com).
2. Создать проект (или выбрать существующий).
3. Включить APIs:
   - **Google+ API** (или People API)
   - **Google Identity Services**
4. Создать **OAuth 2.0 Client ID**:
   - Тип: **Web application**
   - Authorized redirect URIs: `https://sleep-test.kuban-forum.ru/auth/callback/google`
5. Скопировать `Client ID` и `Client Secret`.

### Backend: env-переменные

```bash
# /srv/sleep-test/backend/.env
GOOGLE_CLIENT_ID=xxx.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=GOCSPX-xxx
```

### Бэкенд: эндпоинты (уже готовы)

| Метод | Путь | Описание |
|---|---|---|
| POST | `/auth/google` | Вход через Google ID token (JS SDK) |
| POST | `/auth/link` | Привязка Google аккаунта к существующему |

### Фронт: что восстановить

1. **`GoogleSignInButton.tsx`** — кнопка «Войти с Google» (использует Google Identity Services SDK).
2. Добавить кнопку в `AuthModal.tsx` (после формы email).
3. Добавить Google GSI скрипт в `index.html`:
   ```html
   <script src="https://accounts.google.com/gsi/client" async defer></script>
   ```
4. Инициализация: `google.accounts.id.initialize({ client_id: GOOGLE_CLIENT_ID, callback: handleCredentialResponse })`.
5. Обработка: `api.signInGoogle(id_token)` → JWT → `finishAuth()`.

### Фронт: env-переменная

```bash
VITE_GOOGLE_CLIENT_ID=xxx.apps.googleusercontent.com
```

---

## 2. Яндекс

### Бэкенд: настройка Яндекс OAuth

1. Перейти в [Yandex OAuth](https://oauth.yandex.com).
2. Создать приложение (или использовать существующее).
3. Указать Callback URL: `https://sleep-test.kuban-forum.ru/auth/callback/yandex`.
4. Скопировать `Client ID` и `Client Secret`.

### Backend: env-переменные

```bash
# /srv/sleep-test/backend/.env
YANDEX_CLIENT_ID=xxx
YANDEX_CLIENT_SECRET=xxx
```

### Бэкенд: эндпоинты (уже готовы)

| Метод | Путь | Описание |
|---|---|---|
| POST | `/auth/yandex/init` | Получить URL для редиректа + state |
| GET | `/auth/yandex/status` | Поллинг статуса авторизации |
| GET | `/auth/yandex/callback` | Callback от Яндекса |

### Фронт: что восстановить

1. **`YandexCallbackPage.tsx`** — страница-обработчик callback.
2. Добавить роут в `App.tsx`: `/auth/callback/yandex` → `YandexCallbackPage`.
3. Кнопка «Войти с Яндекс ID» в `AuthModal.tsx`:
   - Вызов `api.yandexInit()` → редирект на `auth_url`.
   - После callback → поллинг `api.yandexStatus(state)` → JWT → `finishAuth()`.

### Важно: REDIRECT_URI

В `backend/services/yandex_auth_service.py:16`:
```python
REDIRECT_URI = "https://app.innercore.art/auth/callback/yandex"
```
**Заменить** на `https://sleep-test.kuban-forum.ru/auth/callback/yandex` для тестового сервера.

---

## 3. VK

### Бэкенд: настройка VK ID

1. Перейти в [VK Developers](https://dev.vk.com).
2. Создать приложение → тип **Standalone** (или **Website**).
3. Указать Callback URL: `https://sleep-test.kuban-forum.ru/auth/callback/vk`.
4. В настройках приложения: включить **VK ID**.
5. Скопировать `Application ID` и `Secret Key`.

### Backend: env-переменные

```bash
# /srv/sleep-test/backend/.env
VK_CLIENT_ID=xxx
VK_CLIENT_SECRET=xxx
```

### Бэкенд: эндпоинты (уже готовы)

| Метод | Путь | Описание |
|---|---|---|
| POST | `/auth/vk/init` | Получить URL для редиректа + PKCE challenge |
| GET | `/auth/vk/status` | Поллинг статуса |
| GET | `/auth/vk/callback` | Callback от VK |

### Фронт: что восстановить

1. **`VkCallbackPage.tsx`** — страница-обработчик callback.
2. Добавить роут в `App.tsx`: `/auth/callback/vk` → `VkCallbackPage`.
3. Кнопка «Войти с VK ID» в `AuthModal.tsx`.

### Важно: REDIRECT_URI

В `backend/services/vk_auth_service.py:27`:
```python
REDIRECT_URI = "https://app.innercore.art/auth/callback/vk"
```
**Заменить** на `https://sleep-test.kuban-forum.ru/auth/callback/vk` для тестового сервера.

### VK: PKCE

VK ID использует PKCE (Proof Key for Code Exchange):
- При `/init` генерируется `code_verifier` → хэшируется в `code_challenge`.
- При обмене кода на токен `code_verifier` отправляется обратно.
- Всё реализовано в `vk_auth_service.py`.

---

## 4. Telegram

### Бэкенд: настройка Telegram Bot

1. Открыть [@BotFather](https://t.me/BotFather) в Telegram.
2. Создать нового бота: `/newbot` → задать имя и username.
3. В настройках бота: включить **Domain Management** → добавить `sleep-test.kuban-forum.ru`.
4. Скопировать токен бота.
5. Создать бота для авторизации (отдельного от основного): `/newbot` → `InnerCore Auth Bot`.
6. В настройках бота: **Menu Button** → URL = `https://sleep-test.kuban-forum.ru`.

### Backend: env-переменные

```bash
# /srv/sleep-test/backend/.env
TELEGRAM_BOT_USERNAME=innercore_auth_bot
TELEGRAM_BOT_BACKEND_SECRET=xxx
```

### Бэкенд: эндпоинты (уже готовы)

| Метод | Путь | Описание |
|---|---|---|
| POST | `/auth/telegram/init` | Получить auth_token + ссылку `t.me/BOT?start=AUTH_TOKEN` |
| GET | `/auth/telegram/status` | Поллинг статуса (Redis) |
| POST | `/auth/telegram/confirm` | Подтверждение от Telegram Mini App |

### Фронт: что восстановить

1. **Telegram Login Widget** или **Telegram Mini App** для подтверждения.
2. Кнопка «Войти с Telegram» в `AuthModal.tsx`:
   - Вызов `api.telegramInit()` → получение `bot_username` + `auth_token`.
   - Редирект: `https://t.me/{bot_username}?start={auth_token}`.
   - Юзер открывает бота → подтверждает → бэкенд получает callback.
   - Фронт поллит `api.telegramStatus(auth_token)` → JWT → `finishAuth()`.

### Telegram: flow

```
1. Фронт → POST /auth/telegram/init → { auth_token, bot_username }
2. Юзер → t.me/{bot_username}?start={auth_token}
3. Бот → /auth/telegram/confirm → Redis записывает { telegram_id, first_name, ... }
4. Фронт → GET /auth/telegram/status?state={auth_token} → { access_token, refresh_token }
```

---

## 5. Общие замечания

### REDIRECT_URI

Для каждого провайдера нужно менять `REDIRECT_URI` в соответствующем сервисе:
- `yandex_auth_service.py` → строка `REDIRECT_URI`
- `vk_auth_service.py` → строка `REDIRECT_URI`

Текущие значения захардкожены на `https://app.innercore.art`. Для `sleep-test.kuban-forum.ru` нужно менять.

### Callback URL на фронте

Каждый провайдер требует callback-страницу на фронте:
- `/auth/callback/google`
- `/auth/callback/yandex`
- `/auth/callback/vk`
- `/auth/callback/telegram` (не нужен — flow через Telegram bot)

### Кнопки в AuthModal

Текущий `AuthModal.tsx` — email-only. Для восстановления соц-кнопок нужно:
1. Раскомментировать/восстановить удалённые компоненты кнопок.
2. Добавить разделитель «или» между email-формой и кнопками.
3. Обработать успешный ответ (JWT) → `finishAuth()`.

### CORS

Бэкенд: `CORS_ORIGINS=["*"]` — для прода нужно сузить до фактического origin.

### Redis

Все провайдеры (кроме Google) используют Redis для хранения state/token:
- `yandex_auth:` — state → user data
- `vk_auth:` — state → user data
- `tg_auth:` — auth_token → user data

Redis уже работает на `127.0.0.1:6379`.

---

## 6. Порядок действий

1. **Яндекс** (самый простой):
   - Настроить приложение в Yandex OAuth.
   - Добавить `YANDEX_CLIENT_ID` + `YANDEX_CLIENT_SECRET` в `.env`.
   - Заменить `REDIRECT_URI` в `yandex_auth_service.py`.
   - Восстановить `YandexCallbackPage.tsx` + роут.

2. **VK** (чуть сложнее — PKCE):
   - Настроить приложение в VK Developers.
   - Добавить `VK_CLIENT_ID` + `VK_CLIENT_SECRET` в `.env`.
   - Заменить `REDIRECT_URI` в `vk_auth_service.py`.
   - Восстановить `VkCallbackPage.tsx` + роут.

3. **Telegram** (без браузерного flow):
   - Создать бота через BotFather.
   - Добавить `TELEGRAM_BOT_USERNAME` + `TELEGRAM_BOT_BACKEND_SECRET` в `.env`.
   - Восстановить кнопку + flow через bot deep-link.

4. **Google** (требует Cloud Console):
   - Создать проект в Google Cloud Console.
   - Добавить `GOOGLE_CLIENT_ID` + `GOOGLE_CLIENT_SECRET` в `.env`.
   - Восстановить `GoogleSignInButton.tsx` + Google GSI SDK.

---

Документ создан: 2026-08-03.
