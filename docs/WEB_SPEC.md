# InnerCore — спецификация веб-фронтенда

> **Назначение.** Этот документ описывает весь функционал приложения InnerCore и
> протокол взаимодействия с backend, чтобы можно было собрать **веб-версию** (лендинг + SPA)
> с функционалом, аналогичным мобильному Flutter-клиенту.
>
> Документ написан стек-агностично: можно реализовать на React / Vue / Svelte / Next и т.д.
> Везде, где упоминается «мобильный клиент», имеется в виду текущее Flutter-приложение в `client/`.
>
> **Статус монетизации.** Google Play Billing в мобильном клиенте отключён (закомментирован,
> см. метки `GOOGLE PLAY BILLING (disabled)` в коде). Серверные механики тарифов/лимитов
> **остаются рабочими** (`/billing/status`, лимиты FREE). Способ оплаты для веба будет выбран
> позже (ЮKassa/Stripe/др.) — пока веб показывает статус и paywall-заглушку.

---

## Для AI-билдера (Emergent) — прочитай первым

**Что ты строишь:** веб-версию InnerCore — (1) маркетинговый **лендинг** и (2) **веб-приложение (SPA)**
с функционалом, идентичным мобильному Flutter-клиенту из `client/`.

**Чего ты НЕ строишь (критично — иначе сломаешь проект):**
- ❌ **НЕ создавай backend.** Бэкенд уже существует — это FastAPI-сервис в папке `backend/`
  (PostgreSQL, Redis, Celery, MinIO, JWT). Веб-фронт обращается к нему по HTTP API из раздела 15.
  Не поднимай новую БД, новую авторизацию, новые модели данных, новый ORM.
- ❌ **НЕ переписывай LLM/анализ.** Анализ снов, чат и карта символов считаются на сервере
  (отдельный LLM-сервис). Фронт только вызывает эндпоинты и рендерит результат.
- ❌ **Не выдумывай эндпоинты.** Используй только те, что в разделе 15. Если чего-то не хватает —
  это фронтовая задача (композиция существующих вызовов), а не повод трогать бэк.

**Источники истины (приоритет при противоречиях):**
1. **Скриншоты** — визуальная истина: компоновка экранов, расположение элементов, ощущение.
2. **Этот документ** — поведение, API-контракты, бизнес-логика, философия, дизайн-язык.
3. **Код Flutter-клиента** (`client/lib/`) — точная деталь, когда нужно (валидации, дефолты,
   интервалы polling). Не порти UI один-в-один — переосмысли под веб, сохранив суть.

**Рекомендуемый стек:** агностично, но удобно — React + Vite + TypeScript (или Next.js); HTTP через
fetch/axios. Главное — корректно говорить с существующим API (раздел 2: обязательный `X-App-Version`,
JWT Bearer, авто-refresh при 401).

**Definition of Done:** чеклист раздела 14 + соответствие философии и дизайн-языку (ниже).
Лендинг продаёт «суть», приложение даёт паритет функций.

---

## Философия и суть продукта (важнее, чем кажется)

InnerCore — это **не дневник снов и не AI-болталка**. Это инструмент **самопознания через сны**,
построенный на **юнгианской глубинной психологии**. Если веб не передаёт этого ощущения — он провалился,
даже при идеальном API.

**Идея.** Сон — послание бессознательного. Записывая сны и получая их разбор, человек постепенно видит
карту собственной психики: повторяющиеся символы, доминирующие архетипы, движение эмоций, фазу
внутреннего пути (индивидуации по Юнгу).

**Юнгианский фундамент** (этим пропитан тон — не academic-сухо, а проживаемо):
- Бессознательное говорит образами и символами.
- **Архетипы**: Тень, Анима/Анимус, Самость и др. — узнаваемые фигуры внутреннего мира.
- **Индивидуация** — путь становления собой; у каждого пользователя есть текущая «фаза».
- Ассистент-аналитик зовётся **Oneiros** (греческое олицетворение сна): спокойный, вдумчивый,
  тёплый проводник, а не клинический эксперт.

**Ключевой цикл продукта:**
```
Запиши сон  →  Получи юнгианский анализ  →  Поговори о нём (чат)
      ↑                                              ↓
Эволюционирующий портрет психики  ←  Карта символов (архетипы)
```
- **Память/портрет.** Сервер копит по всем снам «психологический профиль» (recurring темы, архетипы,
  emotional shift, фаза). Каждый новый сон сопоставляется с прошлым — приложение **помнит тебя и видит
  динамику во времени**. Это главное отличие от обычного AI-чата.
- **Карта снов.** Символы кластеризуются по архетипам в визуальную карту внутреннего мира —
  буквально «атлас бессознательного» пользователя.

**Эмоциональное обещание и тон:**
- Личное святилище, приватность, ноль осуждения. Анонимный старт без регистрационной стены.
- Минимум трения: «Просто запиши свой Сон». Всё опционально (даже онбординг можно пропустить).
- Интонация: спокойная, интроспективная, поэтичная, но читаемая; глубокая, но не претенциозная.
- Лендинг передаёт именно это: тайна снов + строгая основа (Юнг) + современный спокойный продукт.
  **Не** «гадание по снам», **не** эзотерика ради эзотерики.

---

## Дизайн-язык и визуальная идентичность

**Настроение:** ночное, сновидческое, мистичное-но-чистое, современное. Тёмная тема — первоклассный гражданин.

**Цвет:**
- **Бренд-акцент (seed):** глубокий фиолетовый `#673AB7` (Material deep purple). Вся палитра выводится
  из него по схеме Material 3 «from seed» — реализуй и светлую, и тёмную тему.
- **Фирменный градиент сна:** `#FA9042` (тёплый янтарь) → `#8885FF` (барвинково-фиолетовый).
  Это подпись бренда: карточки снов без своего цвета, hero лендинга, ключевые акценты.
- **Тёмные фоны:** глубокие сине-графитовые `#0F1115`, `#10141D`, `#12161F`, `#151923`, `#0D111A`.
- **Палитра архетипов** (цвета узлов карты): `#FFA726`, `#FF7043`, `#AB47BC`, `#7E57C2`, `#42A5F5`,
  `#66BB6A`, `#26A69A`, `#EF5350`, `#8D6E63`, `#78909C`. Конкретный цвет узла приходит в `archetype_color`.
- Каждый сон может иметь свой градиент (`gradient_color_1/2` от LLM); fallback — фирменный градиент выше.

**Форма и материал:**
- Крупные скругления: карточки ~28px, поля ввода ~16px, кнопки-пилюли (полное скругление).
- Мягкие тени, много воздуха.
- **Стекломорфизм:** модалки/онбординг — полупрозрачный слой + backdrop blur (~10px).

**Типографика:** чистый читаемый гротеск; анализ и ответы ассистента — **Markdown** (рендерить
безопасно, с санитизацией HTML).

**Движение:** мягкое и сдержанное (переходы ~180–220ms, плавные контейнеры, пульсация во время анализа).
Никакой резкости.

**Персонализация (повторить в настройках веба):** смена акцентного цвета, переключатель тёмная/светлая
тема, размер шрифта. Локализация **RU + EN**.

**Образность:** луны, звёзды, символы, мягкие свечения, абстрактные «туманности» — без китча.
Ориентир — премиальное приложение для саморефлексии/медитации, а не эзотерический лубок.

---

## 0. TL;DR для разработчика веба

1. Все запросы (кроме 3 служебных) **обязаны** содержать заголовок `X-App-Version` со значением
   ≥ `APP_MIN_VERSION` (сейчас `0.3.2`). Без него backend вернёт **426 Upgrade Required**.
2. Авторизация — **JWT Bearer**. Старт всегда с анонимного входа по `device_id` (генерируется на
   клиенте и хранится локально). Email/Google — опциональный апгрейд анонимного аккаунта.
3. При `401` — обновить токены через `POST /api/v1/auth/refresh` и повторить запрос.
4. Тяжёлые операции (анализ сна, ответ в чате) — **асинхронные**: получаешь `task_id`,
   опрашиваешь статус (polling) или подтягиваешь результат.
5. Карта снов — REST + опционально WebSocket для прогрессивной загрузки.
6. Голосовой ввод — загрузка аудиофайла на `POST /api/v1/audio/transcriptions`, получаешь текст.

---

## 1. Архитектура backend (контекст)

```
Web Client (SPA)  ─┐
Mobile (Flutter)  ─┤──>  FastAPI Backend  <-->  PostgreSQL / Redis / MinIO
                   │            │
                   │            └─> Celery Worker ──> LLM Service (анализ/чат)
                   │                               └─> CometAPI (embeddings, whisper STT)
```

- **Backend**: FastAPI, JWT, PostgreSQL (async SQLAlchemy), Redis (брокер Celery + кэш),
  MinIO (S3), Celery (фоновые задачи).
- **LLM Service**: отдельный сервис-обёртка над Gonka (OpenAI-совместимый) с fallback на CometAPI.
  Веб с ним **не общается напрямую** — только через backend.
- Веб-фронт работает **только** с Backend API.

База: `http://{host}:{port}` (по умолчанию `http://localhost:8000`).
Префикс бизнес-эндпоинтов: `/api/v1`.
Документация бэка вживую: `GET /docs` (Swagger), `GET /redoc`.

---

## 2. Базовые правила работы с API

### 2.1 Обязательный заголовок версии (важно!)

`backend/main.py` содержит `MinVersionMiddleware`. Логика:

- Освобождены от проверки только: `GET /`, `GET /health`, `GET /api/v1/app/version`.
- Для **всех остальных** запросов требуется заголовок `X-App-Version`.
  - Если заголовка нет → `426` с телом `{ "detail": "...", "min_version": "...", "download_url": "..." }`.
  - Если версия < `APP_MIN_VERSION` → тоже `426`.

**Что делать вебу:** на каждый запрос (включая `/auth/*`, `/auth/refresh`) добавлять заголовок:

```
X-App-Version: 0.4.2
```

Значение должно быть ≥ `0.3.2`. Заведите константу версии веб-клиента и держите её ≥ min.

> ⚠️ В мобильном `api_client.dart` запрос `/auth/refresh` отправляется **без** `X-App-Version`
> (потенциальный баг). В вебе ставьте заголовок на **все** запросы без исключений.

### 2.2 Аутентификация запросов

- Заголовок: `Authorization: Bearer <access_token>`.
- Тип токенов JWT: `access` (короткоживущий) и `refresh` (долгоживущий). Сроки задаются в `.env`
  (`JWT_ACCESS_TOKEN_EXPIRE_MINUTES`, `JWT_REFRESH_TOKEN_EXPIRE_DAYS`).
- Сервер **stateless**: токены нигде на сервере не хранятся, разлогин = удаление токенов на клиенте.

### 2.3 Авто-refresh при 401

Паттерн (как в мобильном `ApiClient`):

```
1. Делаем запрос с access-токеном.
2. Если ответ 401 и запрос требует авторизации:
   2.1 POST /api/v1/auth/refresh { refresh_token } (с X-App-Version!)
   2.2 если 200 → сохранить новую пару токенов, повторить исходный запрос
   2.3 если не 200 → разлогин (очистить токены, увести на анонимный старт/экран входа)
```

### 2.4 Прочее

- Тела запросов/ответов — JSON, UTF-8. `Content-Type: application/json` (кроме multipart-загрузок).
- Статусы Celery-задач **регистрозависимы**; клиент должен принимать оба варианта:
  `PENDING`, `STARTED`/`PROCESSING`, `SUCCESS`/`COMPLETED`, `FAILURE`/`FAILED`.
- Типичные коды ошибок: `400` (валидация/бизнес), `401` (нет/невалидный токен),
  `402` (лимит анализов исчерпан), `403` (доступ запрещён/неактивен), `404`, `409` (конфликт),
  `422` (валидация Pydantic), `426` (нужно обновление), `429` (лимит снов в сутки),
  `500/503` (сервер/внешний сервис).

### 2.5 Хранение токенов и device_id на вебе

Мобильный клиент хранит `device_id`, `access_token`, `refresh_token` в secure storage.
Для веба варианты:

- **Рекомендуемо для MVP:** `localStorage` для `device_id` + токенов (просто, переживает перезагрузку).
- **Безопаснее:** хранить `refresh_token` в `httpOnly`-cookie через свой BFF-слой
  (требует доработки, бэкенд сейчас токенов в cookie не ставит). Для старта — `localStorage`.
- `device_id` — сгенерировать `crypto.randomUUID()` один раз, сохранить навсегда (длина ≥ 8).

---

## 3. Аутентификация и аккаунт

Модель: **anonymous-first**. Пользователь сразу работает анонимно; email/Google — это
«апгрейд» того же аккаунта (с переносом данных), а не отдельный вход с нуля.

### 3.1 Поток запуска веб-приложения

```
Старт:
  1. Прочитать device_id из localStorage; если нет → crypto.randomUUID() → сохранить.
  2. Есть сохранённые токены?
       да  → GET /api/v1/users/me (проверить валидность; при 401 → refresh)
       нет → POST /api/v1/auth/anonymous { device_id } → сохранить токены
  3. GET /api/v1/users/me → если profile.onboarding_completed == false
       ИЛИ about_me пустой → показать онбординг.
  4. Перейти на главный экран.
```

### 3.2 Анонимный вход

`POST /api/v1/auth/anonymous`
```json
{ "device_id": "uuid (>=8 симв.)", "platform": "web", "app_version": "0.4.2" }
```
Ответ `200`:
```json
{
  "access_token": "jwt",
  "refresh_token": "jwt",
  "user": { "id": "uuid", "is_anonymous": true, "email": null }
}
```
- Если `device_id` уже существует → возвращаются токены существующего пользователя.
- Ошибки: `400 invalid device_id`.

### 3.3 Регистрация по email

`POST /api/v1/auth/register`
```json
{
  "email": "user@example.com",
  "password": "min8chars",
  "first_name": "Carl",      // опционально
  "last_name": "Jung",       // опционально
  "timezone": "Europe/Moscow" // IANA, по умолчанию "UTC"
}
```
Ответ `201`: `{ "access_token", "refresh_token", "token_type": "bearer" }`.
- На email отправляется **6-значный код** подтверждения.
- Ошибки: `400` email занят; `422` некорректный timezone/пароль (8–128).

> После регистрации/входа выполните **merge** анонимных данных (см. 3.9), затем сохраните
> новые токены вместо анонимных.

### 3.4 Подтверждение email (6-значный код)

`POST /api/v1/auth/verify-email-code`
```json
{ "email": "user@example.com", "code": "123456" }
```
Ответ `200`: `{ "message": "Email verified" }`. Ошибка `400 invalid_or_expired_code`.

Повторная отправка кода: `POST /api/v1/auth/resend-code` `{ "email": "..." }`.

> Также есть «ссылочное» подтверждение: `GET /api/v1/auth/verify-email?token=...`
> и `POST /api/v1/auth/resend-verification`. Для веба основной путь — **код**.
> Подтверждение email **не обязательно** для пользования основными функциями.

### 3.5 Вход по email/паролю

`POST /api/v1/auth/login` `{ "email", "password" }` → токены.
- Ошибки: `401` неверные данные, `403` пользователь неактивен.

### 3.6 Сброс пароля

- `POST /api/v1/auth/forgot-password` `{ "email" }` → письмо (всегда `200`, не раскрывает наличие).
- `POST /api/v1/auth/reset-password` `{ "token", "new_password" }` → `200`.

### 3.7 Google Sign-In (веб)

На вебе используется **Google Identity Services (GIS)** в браузере (НЕ мобильный плагин
`google_sign_in`). Нужно получить **ID token** и отправить его на backend.

Фронт (схема):
```
1. Подключить https://accounts.google.com/gsi/client
2. Инициализировать с client_id (Web OAuth Client ID из Google Cloud Console).
3. Получить credential.id_token из callback (One Tap или кнопка).
4. POST /api/v1/auth/google { id_token }  (+ Authorization: Bearer <анонимный токен>, если есть)
```

`POST /api/v1/auth/google`
```json
{ "id_token": "google_id_token" }
```
Поведение сервера:
- Если Google-аккаунт уже привязан → возвращает токены **существующего** пользователя.
- Иначе: если в заголовке есть Bearer текущего (анонимного) пользователя → **привязывает**
  Google к нему; если нет → создаёт нового пользователя.

Ответ `200`: `{ "access_token", "refresh_token", "token_type": "bearer" }`. Ошибка `400` — невалидный токен.

> Для веба нужен **Web** OAuth Client ID (тип «Web application») в Google Cloud Console
> с корректными Authorized JavaScript origins / redirect URIs. Backend верифицирует `aud`
> по `GOOGLE_CLIENT_ID` — убедитесь, что значения согласованы.

### 3.8 Привязка провайдера к существующему аккаунту

`POST /api/v1/auth/link` (нужен Bearer)
```json
{ "provider": "google", "id_token": "..." }   // provider: "google" | "apple"
```
Ответ `200`: `{ "linked": true, "user": {...}, "provider_identity": {...} }`.
Ошибки: `400 invalid_provider|invalid_token`; `409 identity_already_linked` (привязан к другому)
или `user_already_has_identity`.

### 3.9 Перенос анонимных данных (merge)

При первом входе/регистрации перенесите данные анонимного аккаунта в постоянный:

`POST /api/v1/auth/merge-anonymous` (Bearer = **новый** токен)
```json
{ "anonymous_device_id": "<device_id анонима>" }
```
Ответ `200`: `{ "message": "Anonymous data merged" }` (или «No anonymous account found»).
Переносятся сны, анализы, сообщения и связанные сущности; анонимный аккаунт удаляется.

### 3.10 Прочее

- `POST /api/v1/auth/refresh` `{ "refresh_token" }` → новая пара токенов.
- `POST /api/v1/auth/logout` → `{ "message": ... }` (на самом деле просто удалите токены на клиенте).
- `DELETE /api/v1/auth/account` (Bearer) → каскадно удаляет пользователя и все данные.

---

## 4. Пользователь и онбординг

### 4.1 Текущий пользователь

`GET /api/v1/users/me` (Bearer) →
```json
{
  "id": "uuid",
  "email": "user@email.com | null",
  "is_anonymous": false,
  "email_verified": true,
  "sub_type": "free | trial | pro",
  "linked_providers": ["google"],
  "profile": { "about_me": "...", "onboarding_completed": true }
}
```

### 4.2 Обновление профиля/настроек

`PUT /api/v1/users/me` (Bearer)
```json
{
  "self_description": "Текст «о себе» (<=1000)",  // → profile.about_me
  "timezone": "Europe/Moscow",                    // влияет на суточный лимит снов
  "onboarding_completed": true
}
```
Все поля опциональны (обновляются только переданные). Ответ — обновлённый `UserMeResponse`.

### 4.3 Онбординг (UX)

Мобильный показывает онбординг, если `onboarding_completed == false` **или** `about_me` пустой.
Онбординг — многошаговая модалка, в конце собирает «о себе» (self_description), которое затем
используется как контекст для анализа. По завершении: `PUT /users/me { self_description, onboarding_completed: true }`.

### 4.4 Память пользователя (debug)

`GET /api/v1/users/me/memory` → `{ version, updated_at, content_md }`.
Это «психологический профиль» (user.md), который LLM накапливает и использует. Для UI не обязателен;
можно показать в продвинутых настройках/Pro.

---

## 5. Сны (Dreams)

### 5.1 Объект `DreamResponse`

```json
{
  "id": "uuid",
  "user_id": "uuid",
  "title": "string | null",       // <=64
  "content": "string",            // 10..10000
  "emoji": "string",              // <=10
  "comment": "string",            // <=256
  "recorded_at": "ISO-8601",
  "created_at": "ISO-8601",
  "updated_at": "ISO-8601",
  "has_analysis": false,
  "analysis_status": "saved | analyzing | analyzed | analysis_failed",
  "analysis_error_message": "string | null",
  "gradient_color_1": "#RRGGBB | null",
  "gradient_color_2": "#RRGGBB | null"
}
```

`analysis_status` — производное от статуса анализа, используйте его для отображения карточки:
- `saved` — анализа нет (показать кнопку «Анализировать»).
- `analyzing` — идёт анализ (показать индикатор/пульсацию).
- `analyzed` — готов (есть чат, `has_analysis=true`).
- `analysis_failed` — ошибка (показать ретрай).

### 5.2 Создание сна

`POST /api/v1/dreams`
```json
{ "content": "Текст сна (10..10000)", "title": "опц.", "emoji": "опц.", "comment": "опц." }
```
Ответ `201` — `DreamResponse` (`analysis_status: "saved"`, `has_analysis: false`).
- **Лимит: 5 снов в сутки** (по часовому поясу пользователя) → `429`.
- Анализ **не запускается автоматически** (ручной флоу, см. раздел 6).

**Поведение клиента при создании (повторить на вебе):**
- **Заголовок по умолчанию**, если пользователь не ввёл title — первые 3 слова `content`:
  ```js
  const defaultTitle = content.trim().split(/\s+/).slice(0, 3).join(' ');
  ```
- **Градиент по умолчанию** для карточек без цвета: `gradient_color_1 = #FA9042`,
  `gradient_color_2 = #8885FF` (fallback при `null`).

### 5.3 Список снов

`GET /api/v1/dreams?page=1&page_size=10&date=YYYY-MM-DD`
- `page` ≥ 1, `page_size` 1..100, `date` — опциональный фильтр.
- Ответ: `{ "dreams": [DreamResponse...], "total", "page", "page_size", "total_pages" }`.
- Сортировка: новые сверху. Мобильный показывает 3-колоночную сетку карточек.

### 5.4 Поиск

`GET /api/v1/dreams/search?q=...&mode=semantic`
- `q` — строка (≥1), `mode` = `semantic` (по умолчанию, по эмбеддингам) | `lexical` (по подстроке).
- Ответ: `{ "dreams": [...], "total", "query", "mode" }`.

### 5.5 Получить / обновить / удалить

- `GET /api/v1/dreams/{dream_id}` → `DreamResponse`.
- `PUT` или `PATCH /api/v1/dreams/{dream_id}` — поля `title`, `content`, `emoji`, `comment`,
  `created_at` (можно сдвинуть дату; `422 created_at_cannot_be_in_future` если в будущем).
- `DELETE /api/v1/dreams/{dream_id}` → `{ "message": ... }` (удаляет связанные анализ/сообщения).

---

## 6. Анализ сна (асинхронный)

Один сон → один анализ → одна «комната» чата. Анализ запускается **вручную** (кнопкой).

### 6.1 Запуск анализа

Основной путь (с проверкой лимита) — `POST /api/v1/analyses`:
```json
{ "dream_id": "uuid" }
```
Ответ `202`:
```json
{ "analysis_id": "uuid", "task_id": "string", "status": "pending",
  "message": "Analysis task created. Use task_id to check status." }
```
Ошибки:
- `402 analysis_limit_reached` — у FREE-пользователя кончились анализы недели → показать **Paywall**.
- `404` — сон не найден; `409` — анализ уже существует/выполняется.

> Альтернатива: `POST /api/v1/dreams/{dream_id}/analyze` → возвращает `DreamResponse`
> со статусом `analyzing`. Этот путь **не** проверяет недельный лимит; основной UI
> мобильного использует `POST /analyses` (с лимитом). Рекомендую вебу делать так же.

### 6.2 Отслеживание прогресса

Два механизма (можно комбинировать):

**A. По задаче** — `GET /api/v1/analyses/task/{task_id}`:
```json
{ "task_id": "...", "status": "PENDING|PROCESSING|SUCCESS|FAILURE", "result": "...|null",
  "error": "...|null", "progress": 0 }
```
Polling: интервал ~2 сек, до ~60 попыток. Успех при `SUCCESS|COMPLETED`, ошибка при `FAILURE|FAILED`.

**B. По сну** — `GET /api/v1/dreams/{dream_id}` и смотреть `analysis_status`
(`analyzing` → `analyzed`/`analysis_failed`). Мобильный использует именно этот polling
(каждые 2 сек, до 60 раз) для обновления карточки и заголовка/градиента (их выставляет LLM).

### 6.3 Получить результат анализа

`GET /api/v1/analyses/dream/{dream_id}` →
```json
{ "id": "uuid", "dream_id": "uuid", "user_id": "uuid",
  "result": "Markdown-анализ | null", "status": "completed",
  "error_message": null, "created_at": "...", "completed_at": "..." }
```
- `result` — Markdown (рендерить как разметку).
- Также: `GET /api/v1/analyses/{analysis_id}`, `GET /api/v1/analyses` (список, до 100).

### 6.4 UX-логика нижней панели экрана сна

```
analysis_status == "saved"      → большая кнопка «Анализировать» (POST /analyses)
402 при запуске                  → текст «лимит исчерпан» + кнопка «Перейти на Pro» (Paywall)
analysis_status == "analyzing"   → индикатор прогресса (polling)
analysis_status == "analysis_failed" → текст ошибки + кнопка повторить
analysis_status == "analyzed"    → обычное поле ввода сообщения (чат, раздел 7)
```

### 6.5 Title и градиент от LLM

После анализа LLM возвращает (через backend) не только текст, но и метаданные сна:
`title` и цвета градиента (`gradient_color_1/2`), отражающие эмоциональный тон.
Они приходят в обновлённом `DreamResponse` — фронт просто перечитывает сон и обновляет карточку.

---

## 7. Чат по сну (follow-up)

Доступен после готового анализа (`analyzed`). Это диалог в контексте конкретного сна.

### 7.1 Отправка сообщения

`POST /api/v1/messages`
```json
{ "dream_id": "uuid", "content": "Расскажи подробнее про архетип тени. (1..5000)" }
```
Ответ `202`:
```json
{ "task_id": "string", "status": "processing",
  "user_message": { "id", "user_id", "dream_id", "role": "user", "content", "created_at" } }
```
Сразу добавьте `user_message` в ленту (оптимистично), затем дождитесь ответа ассистента.

### 7.2 Статус задачи ответа

`GET /api/v1/messages/task/{task_id}` → `{ "task_id", "status", "result"?, "error"? }`.
Polling до готовности (`SUCCESS`/`COMPLETED`), затем перечитать историю.

### 7.3 История чата

`GET /api/v1/messages/dream/{dream_id}?limit=50&offset=0` (limit 1..200) →
```json
{ "messages": [ { "id", "user_id", "dream_id", "role": "user|assistant", "content", "created_at" } ],
  "total": 12 }
```
Сортировка: старые первыми. `content` ассистента — Markdown.

---

## 8. Карта снов (Dream Map)

Символическая 2D/3D-карта: узлы (символы из снов), кластеры (по архетипам), фильтры архетипов.
Это «премиальная» фича (для FREE — за Paywall, см. раздел 10).

### 8.1 Получить карту

`GET /api/v1/map/{user_id}` (Bearer; `user_id` должен совпадать с текущим, иначе `403`).
Query-параметры (все опциональны, есть дефолты):
`n_neighbors` (2..50, деф. 15), `min_dist` (0..0.99, 0.02), `cluster_method` (`dbscan`|`fallback`),
`force_refresh` (bool), `dispersion` (0.1..5.0, 1.0), `jitter` (0..0.2, 0.03).

Ответ `DreamMapResponse`:
```json
{
  "nodes": [{
    "id": "string", "symbol_name": "string", "display_label": "string",
    "x": 0.0, "y": 0.0, "z": 0.0,            // x,y ∈ [0,1]; z ∈ [-1,1]
    "cluster_id": 0, "cluster_label": "string",
    "archetype_color": "#RRGGBB",
    "cosine_sim_to_center": 0.0, "size_weight": 0.0,
    "occurrence_count": 1, "dream_count": 1,
    "last_seen_at": "ISO", "preview_text": "string",
    "related_archetypes": ["string"]
  }],
  "clusters": [{ "id": 0, "label": "string", "color": "#RRGGBB", "count": 0,
                 "center": { "x": 0.0, "y": 0.0 } }],
  "archetype_filters": ["string"],   // полный набор архетипов для фильтра
  "meta": { "total_nodes": 0, "total_clusters": 0, "cached": false,
            "computed_with": "string", "cluster_method": "string", "min_nodes_required": 0 }
}
```
Отрисовка: координаты нормированы в [0,1] — масштабируйте под холст. Цвет узла = `archetype_color`.
Размер = `size_weight`. Область **ограничена** (без бесконечного зацикленного скролла).

### 8.2 Деталь символа

`GET /api/v1/map/{user_id}/symbol/{symbol_id}` → `DreamMapSymbolDetailResponse`
(вкл. `related_symbols`, `occurrences: [{ dream_id, date, text_preview }]`). `404` если не найден.

### 8.3 Прогрессивная загрузка (опционально)

WebSocket: `GET /api/v1/map/{user_id}/stream?token=<access_token>&n_neighbors=...`
- Токен передаётся **в query** (`token=...`), а не в заголовке.
- Сервер шлёт JSON-сообщения батчами; при ошибке — `{ "type": "error", "detail": "..." }`.
- Коды закрытия: `4401` (нет/невалидный токен), `4403` (forbidden), `4404` (user not found).
- Для MVP можно обойтись REST `GET /map/{user_id}` + кнопка «обновить» (`force_refresh=true`).

---

## 9. Статистика

`GET /api/v1/stats/me` (Bearer) →
```json
{
  "total_dreams": 150,
  "streak_days": 14,
  "dreams_by_weekday": { "Mon": 20, "Tue": 25, "...": 0 },
  "dreams_last_14_days": [ { "date": "YYYY-MM-DD", "count": 2 } ],
  "archetypes_top": [ { "name": "Тень", "count": 12 } ],
  "avg_time_of_day": "23:30 | null"
}
```
Используйте для дашборда профиля (стрик, график за 14 дней, топ архетипов).

---

## 10. Тарифы, лимиты и Paywall

### 10.1 Статус подписки

`GET /api/v1/billing/status` (Bearer) →
```json
{
  "sub_type": "free | trial | pro",
  "sub_expires_at": "ISO | null",
  "trial_days_left": 0,
  "analyses_left_this_week": 2,        // только для free; иначе null
  "active_subscription": { "product_id": "pro_monthly", "expires_at": "ISO" } | null
}
```
- `hasFullAccess` (доступ к Pro-фичам) = `sub_type` ∈ {`pro`, `trial`}.
- Этот эндпоинт **работает без Google Play** — используйте его как источник истины о тарифе.

### 10.2 Модель тарифов

| Тариф | Запись снов | Анализы | Чат по сну | Карта | Память (user.md) |
|---|---|---|---|---|---|
| FREE | ∞ | 2 / неделя | ❌ (Paywall) | ❌ (Paywall) | ❌ |
| TRIAL (7 дней) | ∞ | ∞ | ✅ | ✅ | ✅ |
| PRO | ∞ | ∞ | ✅ | ✅ | ✅ |

- Недельный счётчик анализов для FREE сбрасывается раз в 7 дней (серверная логика).
- TRIAL выдаётся при первой регистрации (email/Google); существующим — нет.

### 10.3 Триггеры Paywall (для FREE)

```
- Нажатие «Анализировать» при исчерпанном лимите → POST /analyses вернёт 402 → Paywall
  (заголовок «лимит исчерпан»).
- Нажатие «Чат»  (FREE)  → Paywall.
- Нажатие «Карта» (FREE) → Paywall.
```
Фичи **видны** в интерфейсе, но при клике показывают Paywall (не скрыты).

### 10.4 Оплата на вебе (пока не реализована)

- Мобильная покупка через Google Play **отключена** (в вебе она и не применима).
- Серверные эндпоинты `POST /billing/verify-purchase` и `POST /billing/webhook`
  специфичны для Google Play (`verify-purchase` без ключей вернёт `503`). Для веба они **не используются**.
- **Что делает веб сейчас:** показывает `billing/status`, гейтит фичи, на Paywall — заглушку
  «оплата скоро будет доступна».
- **Точка расширения:** при выборе провайдера (ЮKassa/Stripe/…) добавить на бэке эндпоинт
  верификации платежа, который проставляет `users.sub_type='pro'` и `sub_expires_at`
  (по аналогии с `verify_purchase` в `backend/services/billing_service.py`), и на фронте — флоу оплаты.

---

## 11. Голосовой ввод (транскрипция)

`POST /api/v1/audio/transcriptions` (Bearer, `multipart/form-data`):
- `file` (обязательно) — аудиофайл.
- `language` (опц.), `prompt` (опц.).

Ответ `200`:
```json
{ "text": "распознанный текст", "partial": false,
  "segments_total": 1, "segments_ok": 1, "segments_failed": 0 }
```
- `partial=true` — часть сегментов не распозналась (длинное аудио бьётся на чанки).
- Ошибки: `400` пустой/битый файл, `503` сервис недоступен, `500` не сконфигурирован.

**Реализация на вебе:** запись через `MediaRecorder` → `Blob` (например `audio/webm` или `m4a`)
→ `FormData` с полем `file` → POST. Полученный `text` подставить в поле ввода сна
(пользователь может отредактировать перед сохранением).

---

## 12. Версионирование клиента

- `GET /api/v1/app/version` → `{ "version": "0.4.2", "download_url": "..." }` (без авторизации,
  освобождён от проверки версии).
- Веб может опционально сверять свою версию и показывать баннер «доступно обновление».
- Главное — слать `X-App-Version` ≥ `APP_MIN_VERSION` на каждом запросе (см. 2.1).

---

## 13. Карта экранов: мобильный → веб

| Мобильный экран (`client/lib/screens`) | Веб-страница/роут | Назначение |
|---|---|---|
| `startup_splash_screen` | загрузка/бутстрап | Анонимный вход, проверка токенов |
| `onboarding_screen` | `/onboarding` (модалка) | Сбор «о себе», `onboarding_completed` |
| `login_screen` / `email_login` / `email_register` / `verify_email` | `/login`, `/register`, `/verify` | Email + Google вход/регистрация |
| `main_chat_screen` (табы: сетка/поиск/карта/профиль) | `/` (дашборд) + нав | Лента снов 3-кол., поле создания сна, поиск, навигация |
| `analysis_chat_screen` | `/dream/:id` | Сон + анализ (кнопка/прогресс) + чат |
| `dream_map_screen` | `/map` | Карта символов |
| `profile_screen` | `/profile` | Профиль, тариф, настройки, привязка аккаунта |
| `paywall_screen` | `/paywall` (модалка) | Тарифы (сейчас — заглушка оплаты) |

Главный экран (`main_chat_screen`) совмещает: ленту снов (сетка карточек), строку создания сна
(текст + голос), поиск и нижнюю навигацию (сны / карта / профиль).

---

## 14. Чеклист паритета функционала (Definition of Done для веба)

- [ ] Анонимный старт по `device_id`, заголовок `X-App-Version` на всех запросах.
- [ ] Авто-refresh токенов при `401`.
- [ ] Email регистрация/вход + подтверждение по 6-значному коду + сброс пароля.
- [ ] Google Sign-In через GIS (web client id) → `POST /auth/google`.
- [ ] Merge анонимных данных при первом входе.
- [ ] CRUD снов: создание (лимит 5/сут → 429), список с пагинацией, фильтр по дате, поиск (semantic/lexical).
- [ ] Дефолтный заголовок (первые 3 слова) и дефолтный градиент `#FA9042 → #8885FF`.
- [ ] Ручной запуск анализа кнопкой, polling прогресса, рендер Markdown-результата.
- [ ] Title/градиент сна обновляются после анализа.
- [ ] Чат по сну: отправка, polling ответа, история, Markdown.
- [ ] Карта снов: узлы/кластеры/фильтры, деталь символа, «обновить».
- [ ] Статистика профиля.
- [ ] Голосовой ввод → транскрипция → текст в поле сна.
- [ ] Тариф из `billing/status`, гейтинг чат/карта/анализ, Paywall-заглушка.
- [ ] Локализация RU + EN.
- [ ] Обработка `426` (предложить обновиться / поднять версию веба).

---

## 15. Полный справочник эндпоинтов

> Все, кроме `GET /`, `GET /health`, `GET /api/v1/app/version`, требуют заголовок `X-App-Version`.
> «Auth: ✓» — нужен `Authorization: Bearer`.

| Метод | Путь | Auth | Назначение |
|---|---|---|---|
| GET | `/` | — | Статус сервиса |
| GET | `/health` | — | Health-check |
| GET | `/api/v1/app/version` | — | Версия и ссылка на скачивание |
| POST | `/api/v1/auth/anonymous` | — | Анонимный вход по device_id |
| POST | `/api/v1/auth/register` | — | Регистрация email/пароль (+6-значный код) |
| POST | `/api/v1/auth/login` | — | Вход email/пароль |
| POST | `/api/v1/auth/refresh` | — | Обновление токенов |
| GET | `/api/v1/auth/verify-email` | — | Подтверждение email по ссылке (`?token=`) |
| POST | `/api/v1/auth/verify-email-code` | — | Подтверждение email по 6-значному коду |
| POST | `/api/v1/auth/resend-code` | — | Повторная отправка кода |
| POST | `/api/v1/auth/resend-verification` | — | Повторная отправка письма-ссылки |
| POST | `/api/v1/auth/forgot-password` | — | Запрос сброса пароля |
| POST | `/api/v1/auth/reset-password` | — | Сброс пароля по токену |
| POST | `/api/v1/auth/google` | (опц.) | Google Sign-In по id_token |
| POST | `/api/v1/auth/link` | ✓ | Привязка Google/Apple |
| POST | `/api/v1/auth/merge-anonymous` | ✓ | Перенос данных анонима |
| POST | `/api/v1/auth/logout` | (опц.) | Логический выход |
| DELETE | `/api/v1/auth/account` | ✓ | Удаление аккаунта |
| GET | `/api/v1/users/me` | ✓ | Текущий пользователь |
| PUT | `/api/v1/users/me` | ✓ | Обновить профиль/настройки |
| GET | `/api/v1/users/me/memory` | ✓ | Память пользователя (debug) |
| POST | `/api/v1/dreams` | ✓ | Создать сон (лимит 5/сут) |
| GET | `/api/v1/dreams` | ✓ | Список снов (пагинация, дата) |
| GET | `/api/v1/dreams/search` | ✓ | Поиск (semantic/lexical) |
| GET | `/api/v1/dreams/{id}` | ✓ | Получить сон |
| PUT/PATCH | `/api/v1/dreams/{id}` | ✓ | Обновить сон |
| POST | `/api/v1/dreams/{id}/analyze` | ✓ | Ручной запуск анализа (без лимита) |
| DELETE | `/api/v1/dreams/{id}` | ✓ | Удалить сон |
| POST | `/api/v1/analyses` | ✓ | Запросить анализ (лимит → 402) |
| GET | `/api/v1/analyses` | ✓ | Список анализов |
| GET | `/api/v1/analyses/task/{task_id}` | ✓ | Статус задачи анализа |
| GET | `/api/v1/analyses/dream/{dream_id}` | ✓ | Анализ по сну |
| GET | `/api/v1/analyses/{analysis_id}` | ✓ | Анализ по id |
| POST | `/api/v1/messages` | ✓ | Сообщение в чат по сну |
| GET | `/api/v1/messages/dream/{dream_id}` | ✓ | История чата |
| GET | `/api/v1/messages/task/{task_id}` | ✓ | Статус задачи ответа |
| GET | `/api/v1/map/{user_id}` | ✓ | Карта снов |
| GET | `/api/v1/map/{user_id}/symbol/{symbol_id}` | ✓ | Деталь символа |
| WS | `/api/v1/map/{user_id}/stream?token=` | ✓ (query) | Прогрессивная карта |
| GET | `/api/v1/stats/me` | ✓ | Статистика |
| POST | `/api/v1/audio/transcriptions` | ✓ | Транскрипция аудио (multipart) |
| GET | `/api/v1/billing/status` | ✓ | Статус тарифа/лимитов |
| POST | `/api/v1/billing/verify-purchase` | ✓ | (Google Play, на вебе не используется → 503 без ключей) |
| POST | `/api/v1/billing/webhook` | — | (Google Play RTDN, на вебе не используется) |

---

## 16. Примечания и подводные камни

- **Часовой пояс** пользователя влияет на суточный лимит снов (5/сут). Передавайте корректный
  IANA-`timezone` в профиль.
- **Подтверждение email не блокирует** основные функции (анонимные и неподтверждённые работают).
- **CORS**: добавьте origin веб-приложения в `CORS_ORIGINS` бэкенда (`.env`).
- **Markdown**: `result` анализа и `content` сообщений ассистента — Markdown, рендерьте безопасно
  (санитизация HTML).
- **Polling vs WS**: для анализа/чата — polling (просто и надёжно). Для карты — REST достаточно,
  WS опционален.
- Бэкенд-документация всегда актуальна в Swagger: `GET /docs`.
```
