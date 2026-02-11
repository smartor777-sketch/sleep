# JungAI — ТЗ на интеграцию привязки аккаунта через Google / Apple (без паролей)
Версия: 1.0  
Статус: для разработки  
Цель: пользователь работает “без регистрации” (анонимный UUID), а при желании — в профиле нажимает “Привязать аккаунт” (Google/Apple). Привязка происходит через системную авторизацию, без пароля и без email verification.

---

## 1) Контекст и цели

### 1.1 Что уже есть
- Backend: FastAPI, JWT, PostgreSQL, Redis, Celery, MinIO.
- Реализованы: auth (email/password + JWT), CRUD снов, анализ через Celery, один анализ на сон.
- Frontend: Flutter MVP с чатами, профилем, темной темой, accentColor.

### 1.2 Цели интеграции
1) **Убрать необходимость логина/регистрации в UX**: пользователь сразу пользуется приложением.
2) Добавить **опциональную привязку** аккаунта:
   - iOS: Sign in with Apple
   - Android: Sign in with Google
3) Обеспечить надежное сопоставление пользователя на бэке:
   - по анонимному `device_id` (UUID, хранится на устройстве)
   - или через Apple/Google `sub` (provider user id)
4) Подготовить основу под оплату/лимиты (проверки будут на бэке).

---

## 2) Термины и сущности

- **Anonymous user** — пользователь, созданный на бэке по `device_id`.
- **Provider** — `google` или `apple`.
- **Provider identity** — связка `provider + provider_subject (sub)` на конкретного пользователя.
- **Link** — операция привязки provider identity к текущему пользователю.
- **Merge** — опциональная операция объединения аккаунтов (в ТЗ описана как правило, но в MVP можно “запретить” и возвращать конфликт).

---

## 3) Требования безопасности (обязательные)
1) **Никаких секретов OAuth в мобильном приложении** (client secret хранится на бэке, если нужен).
2) Токены провайдеров (id_token) обязательно валидируются:
   - подпись (JWKS),
   - issuer,
   - audience (client_id),
   - срок действия,
   - наличие `sub`.
3) Любая привязка выполняется **только для аутентифицированного пользователя** (по нашему JWT).
4) Защита от повторной привязки:
   - если provider identity уже привязана к другому пользователю → конфликт.
5) Все чувствительные данные логируются без токенов (не писать id_token в логи).

---

## 4) Backend — изменения БД

### 4.1 Таблица users (минимально)
Добавить поля (если нет):
- `id UUID PK`
- `created_at TIMESTAMP`
- `email TEXT NULL` (может быть пустым у анонимного)
- `is_anonymous BOOLEAN NOT NULL DEFAULT true`
- `device_id TEXT UNIQUE NULL` (для анонимного входа; может стать NULL после привязки — по решению)
- `last_login_at TIMESTAMP NULL`

### 4.2 Таблица oauth_identities
Новая таблица:
- `id UUID PK`
- `user_id UUID FK(users.id) ON DELETE CASCADE`
- `provider TEXT NOT NULL CHECK(provider IN ('google','apple'))`
- `provider_subject TEXT NOT NULL`  (sub)
- `email TEXT NULL` (email от провайдера, если есть)
- `created_at TIMESTAMP NOT NULL DEFAULT now()`
- Уникальность: `UNIQUE(provider, provider_subject)`
- Индекс: `(user_id)`

### 4.3 (Опционально) Таблица auth_sessions / refresh_tokens
Если refresh-токены уже реализованы — оставить как есть. Если нет, внедрить refresh по схеме:
- `refresh_tokens(id, user_id, token_hash, created_at, expires_at, revoked_at, device_info)`
(или иной текущий механизм)

---

## 5) Backend — API (контракты)

### 5.1 Анонимная авторизация (без экрана логина)
**POST** `/api/v1/auth/anonymous`

Request:
```json
{
  "device_id": "uuid-string",
  "platform": "ios|android",
  "app_version": "1.0.0"
}

Response 200:

{
  "access_token": "jwt",
  "refresh_token": "jwt-or-opaque",
  "user": {
    "id": "uuid",
    "is_anonymous": true,
    "email": null
  }
}

Логика:
	•	Если device_id уже существует → вернуть токены существующего user.
	•	Если нет → создать нового user (is_anonymous=true, device_id=device_id) → вернуть токены.

Ошибки:
	•	400 invalid device_id
	•	500 internal

⸻

5.2 Привязка Google/Apple (основной endpoint)

POST /api/v1/auth/link

Headers:
	•	Authorization: Bearer <access_token>

Request:

{
  "provider": "google|apple",
  "id_token": "provider_id_token_string"
}

Response 200 (успешно привязано):

{
  "linked": true,
  "user": {
    "id": "uuid",
    "is_anonymous": false,
    "email": "user@email.com"
  },
  "provider_identity": {
    "provider": "google",
    "provider_subject": "xxxx",
    "email": "user@email.com"
  }
}

Ошибки:
	•	401 unauthorized (нет/невалидный наш JWT)
	•	400 invalid_provider / invalid_token / token_expired / audience_mismatch
	•	409 identity_already_linked (provider+sub уже привязан к другому user)
	•	409 user_already_has_identity (если хотим запретить 2 google-аккаунта на одного user)
	•	500 internal

Логика:
	1.	Валидация provider.
	2.	Валидация id_token (см. раздел 6).
	3.	Извлечь sub (provider_subject) и email (если есть).
	4.	Проверить oauth_identities:
	•	если существует (provider,sub) и user_id != current_user_id → 409 conflict
	•	если существует и user_id == current_user_id → идемпотентно вернуть успех
	5.	Создать oauth_identity и привязать к пользователю.
	6.	Обновить user:
	•	is_anonymous=false
	•	email можно заполнить email провайдера, если email у пользователя пустой
	7.	Вернуть успех.

⸻

5.3 Получить текущего пользователя

GET /api/v1/users/me

Headers: Authorization

Response 200:

{
  "id": "uuid",
  "email": "user@email.com",
  "is_anonymous": false,
  "linked_providers": ["google","apple"],
  "profile": {
    "about_me": "..."
  }
}


⸻

5.4 (Опционально) Отвязка

MVP можно не делать. Если делать:
DELETE /api/v1/auth/link/{provider}
Правило: запрещено отвязать последний метод восстановления, если нет другого.

⸻

6) Backend — валидация Google / Apple токенов (требования)

6.1 Google ID Token

Проверки:
	•	iss должен быть https://accounts.google.com или accounts.google.com
	•	aud должен совпадать с GOOGLE_CLIENT_ID
	•	exp не истёк
	•	подпись валидируется по JWKS Google
	•	достать sub, email, email_verified (если есть)

Конфиг:
	•	GOOGLE_CLIENT_ID (как в мобильном приложении)
	•	(если понадобится server auth code flow) — GOOGLE_CLIENT_SECRET (но для id_token обычно не нужен)

6.2 Apple ID Token

Проверки:
	•	iss должен быть https://appleid.apple.com
	•	aud должен совпадать с APPLE_SERVICE_ID или APPLE_BUNDLE_ID (в зависимости от настройки)
	•	exp не истёк
	•	подпись валидируется по JWKS Apple
	•	достать sub, email (email может приходить только первый раз), email_verified (если есть)

Конфиг:
	•	APPLE_CLIENT_ID (bundle id / service id)
	•	(опционально) APPLE_TEAM_ID, APPLE_KEY_ID, приватный ключ — если будет делаться server-to-server verification или token exchange (для MVP link по id_token достаточно).

⸻

7) Frontend (Flutter) — требования и изменения

7.1 Хранилище (обязательное)

Использовать secure storage:
	•	iOS: Keychain
	•	Android: Keystore

Хранить:
	•	device_id (UUID)
	•	access_token
	•	refresh_token
	•	theme_mode (можно и в обычном storage, но допустимо и в secure)
	•	accent_color (можно в обычном storage)

7.2 Поток запуска приложения
	1.	При старте:
	•	если нет device_id → сгенерировать UUID v4 → сохранить
	2.	Вызвать /auth/anonymous → получить токены → сохранить
	3.	Открыть основной экран чата (без LoginScreen)
	4.	При 401 на API → refresh → повтор

7.3 Экран профиля — кнопки привязки

В ProfileScreen:
	•	Показать статус:
	•	“Гость” (если is_anonymous=true)
	•	“Аккаунт привязан” + список провайдеров (если linked)
	•	Кнопки:
	•	iOS: Sign in with Apple
	•	Android: Continue with Google
	•	(Опционально) на обеих платформах можно показывать обе кнопки, но UX лучше платформенный

Поведение:
	•	Пользователь нажимает кнопку → открывается системный провайдер → получаем id_token → отправляем на бэк /auth/link с нашим Authorization → обновляем me → UI обновляется.

7.4 Пакеты Flutter (рекомендация)
	•	flutter_secure_storage
	•	sign_in_with_apple
	•	google_sign_in
	•	dio или http (единый API клиент)
	•	(опционально) uuid

7.5 Ошибки UI
	•	Если /auth/link вернул 409 identity_already_linked:
	•	показать диалог: “Этот аккаунт уже привязан к другому профилю.”
	•	(опционально) предложить “Войти в тот аккаунт” — это потребует merge/replace flow (в MVP можно не делать)
	•	Если токен провайдера невалиден:
	•	“Не удалось подтвердить аккаунт. Попробуйте ещё раз.”

⸻

8) Правила объединения аккаунтов (Merge policy)

MVP-правило (простое и безопасное):
	•	Если provider identity уже привязана к другому user → 409 и ничего не делаем.

Расширение (после MVP):
	•	Разрешить “переключиться” на существующий аккаунт:
	•	клиент повторно авторизуется у провайдера
	•	бэк понимает, что identity принадлежит user_B
	•	бэк выдаёт токены user_B (по явному запросу POST /auth/switch), а user_A можно пометить “orphan” или слить данные.

⸻

9) Изменения в существующем backend auth

Если уже есть email/password:
	•	Оставить как есть (для админки/веба/альтернативы).
	•	Но для мобильного MVP — убрать экран логина и заменить на anonymous flow.

⸻

10) Набор задач (чеклист разработки)

Backend
	•	Миграции: users(device_id,is_anonymous) + oauth_identities
	•	POST /auth/anonymous
	•	POST /auth/link
	•	GET /users/me (добавить linked_providers)
	•	Реализация валидации Google id_token (JWKS + claims)
	•	Реализация валидации Apple id_token (JWKS + claims)
	•	Тесты:
	•	anonymous create + reuse
	•	link success
	•	link idempotent
	•	link conflict 409

Flutter
	•	Secure storage: device_id + tokens
	•	Startup flow: anonymous auth → main chat
	•	API client с авто-refresh при 401
	•	Profile UI: кнопки Apple/Google + статус привязки
	•	Вызов /auth/link с id_token
	•	Обновление state (user.is_anonymous, linked providers)
	•	UX ошибки

⸻

11) Acceptance Criteria (готово, когда)
	1.	Установка приложения → пользователь сразу в чате, без логина.
	2.	Бэк создаёт пользователя по device_id, выдаёт токены.
	3.	В профиле видно “Гость” и кнопки “Привязать Apple/Google”.
	4.	После привязки:
	•	user.is_anonymous=false
	•	в /users/me отображается linked provider
	•	повторное нажатие “Привязать” не ломает (идемпотентно)
	5.	Попытка привязать уже занятый provider-account → 409 и понятное сообщение.
	6.	Работает на iOS симуляторе/устройстве и Android эмуляторе/устройстве.

⸻

12) Примечания по приватности
	•	Не собирать device identifiers платформы (IDFA/GAID) — только случайный UUID.
	•	Email от провайдера хранить только если реально нужно (можно хранить, но не показывать публично).
	•	Минимизировать логи.
