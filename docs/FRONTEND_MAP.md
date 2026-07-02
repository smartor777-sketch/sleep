# FRONTEND_MAP.md — карта веб-клиента `frontend/`

Снимок состояния после коммита `1f25510` (импорт из `origin/frontend`).
Цель документа: дать однозначное понимание, как веб-клиент устроен и что он ждёт от бэкенда, чтобы можно было адаптировать его под наш существующий FastAPI без догадок.

---

## 1. Стек и сборка

| Слой | Что используется |
|---|---|
| Бандлер | Vite 5 (`vite.config.ts`) |
| Язык | TypeScript 5, JSX `react-jsx`, `strict: true` |
| UI | React 18, Tailwind CSS 3, lucide-react (иконки), react-markdown + remark-gfm |
| Router | react-router-dom 6 (BrowserRouter) |
| Стейт | Zustand 5 |
| HTTP | axios 1.7 |
| Дев-сервер | `vite --host 0.0.0.0 --port 3000`, `strictPort: true`, `hmr.clientPort: 443` (тоннельный сценарий) |
| Прод-билд | `tsc --noEmit && vite build` → `frontend/dist/` |

Скрипты: `npm start` / `npm run dev` / `npm run build` / `npm run preview`.

Пути: `@/*` → `src/*` (через `tsconfig.json`).

---

## 2. Точка входа и роутинг

```
main.tsx → initSettingsFromStorage() → <BrowserRouter><App /></BrowserRouter>
App.tsx → setApiHandlers({onUpgradeRequired, onForceLogout}) → bootstrap()
        → пока bootstrapping → <Splash />
        → дальше <Layout> + <Routes>
```

Маршруты (`App.tsx`):

| Path | Page |
|---|---|
| `/` | `DreamsPage` — список снов + composer |
| `/dream/:id` | `DreamPage` — карточка сна, анализ, чат |
| `/map` | `MapPage` — карта символов |
| `/search` | `SearchPage` — поиск (semantic/lexical) |
| `/profile` | `ProfilePage` — профиль, статы, биллинг, настройки |
| `*` | редирект на `/` |

Поверх маршрутов: `<OnboardingModal />`, `<PaywallModal />`, `<AuthModal />` (вызывается из `ProfilePage`).

---

## 3. Конфигурация и env-переменные

Vite читает `import.meta.env`. Используются:

| Переменная | Дефолт | Зачем |
|---|---|---|
| `VITE_API_BASE_URL` | `http://89.125.77.243:8080` | Базовый URL бэкенда. Текущий дефолт — наш тестовый IP-тоннель. **Для прода/dev переопределяется через `.env` или окружение.** |
| `VITE_APP_VERSION` | `0.4.2` | Уходит в `X-App-Version` на каждом запросе. **Должна совпадать с `client/lib/version.dart` и с `APP_LATEST_VERSION` в `backend/main.py`.** |

`.env.example` в репо отсутствует — стоит создать (минимум с этими двумя ключами).

---

## 4. API-клиент (`src/lib/api.ts`)

### Базовое поведение
- Каждый запрос несёт заголовок `X-App-Version: <VITE_APP_VERSION>`.
- JWT в `Authorization: Bearer <access_token>`, кроме запросов с `__skipAuth: true` в config (login/register/anon/refresh/verify/resend/forgot).
- На `401` — единственная попытка `tryRefresh()` (single-flight через переменную `refreshing: Promise|null`), повтор оригинала; при провале — `clearTokens()` + `onForceLogout()`.
- На `426 Upgrade Required` — вызывает `onUpgradeRequired(info)` (фронт показывает баннер).
- Все ошибки оборачиваются в `ApiError { status, data, detail }`.

### LocalStorage-ключи (важно знать при отладке)
| Ключ | Значение |
|---|---|
| `innercore.device_id` | UUID устройства (создаётся через `crypto.randomUUID`, fallback на самописный) |
| `innercore.access_token` | JWT access |
| `innercore.refresh_token` | JWT refresh |
| `innercore.settings.v1` | JSON `{theme, accentId, fontSize, lang}` (см. §9) |

### Bootstrap-флоу (`store.ts → bootstrap()`)
1. Гарантируем device_id.
2. Если есть `access_token` → `GET /users/me`. Если падает — fallback на `POST /auth/anonymous`, потом `/users/me`.
3. Если токенов нет → `POST /auth/anonymous`, потом `/users/me`.
4. Фоном (не блокируя UI) — `GET /billing/status`.
5. Если `user.profile.onboarding_completed === false` или `about_me` пустой → открыть `OnboardingModal`.
6. Любые сетевые сбои — `console.warn`, UI всё равно ставит `ready: true`.

---

## 5. Эндпоинты, которые ждёт фронт

Полный список вызовов `api.*` (всё с префиксом `/api/v1`):

### Auth
| Метод | Путь | Тело / параметры | Где зовётся |
|---|---|---|---|
| GET | `/app/version` | — | (не вызывается фронтом напрямую; используется для 426 ответа от бэка) |
| POST | `/auth/anonymous` | `{device_id, platform: "web", app_version}` | `bootstrap`, `signOut` |
| POST | `/auth/register` | `{email, password, first_name?, last_name?, timezone?}` | `AuthModal` |
| POST | `/auth/login` | `{email, password}` | `AuthModal` |
| POST | `/auth/refresh` | `{refresh_token}` | автоматически при 401 |
| POST | `/auth/verify-email-code` | `{email, code}` | `AuthModal` |
| POST | `/auth/resend-code` | `{email}` | `AuthModal` |
| POST | `/auth/forgot-password` | `{email}` | `AuthModal` |
| POST | `/auth/reset-password` | `{token, new_password}` | (UI ещё нет — экран `/reset-password?token=…` зайдёт позже) |
| POST | `/auth/google` | `{id_token}` (с опциональным Bearer) | (UI Google sign-in зайдёт позже) |
| POST | `/auth/link` | `{provider: 'google'\|'apple', id_token}` | (UI кнопки «привязать провайдера» зайдут позже) |
| POST | `/auth/merge-anonymous` | `{anonymous_device_id}` | сразу после успешного register/login |
| DELETE | `/auth/account` | — | `ProfilePage` |
| POST | `/auth/logout` | — | `signOut` |

### Users
| Метод | Путь | Тело | Где |
|---|---|---|---|
| GET | `/users/me` | — | `bootstrap`, `refreshUser` |
| PUT | `/users/me` | `{self_description?, timezone?, onboarding_completed?}` | `OnboardingModal`, `ProfilePage` |

### Dreams
| Метод | Путь | Параметры | Где |
|---|---|---|---|
| POST | `/dreams` | `{content, title?, emoji?, comment?}` | `DreamsPage` (создать) |
| GET | `/dreams` | `?page, page_size, date` | `loadDreams`, `DreamsPage` |
| GET | `/dreams/search` | `?q&mode=semantic\|lexical` | `SearchPage` |
| GET | `/dreams/{id}` | — | `DreamPage`, `DreamsPage` (после создания) |
| PATCH | `/dreams/{id}` | `{title?, content?, emoji?, comment?, created_at?}` | `DreamPage` (редактирование) |
| DELETE | `/dreams/{id}` | — | `DreamPage` |

### Analyses
| Метод | Путь | Тело | Где |
|---|---|---|---|
| POST | `/analyses` | `{dream_id}` | `DreamPage` (запуск анализа) |
| GET | `/analyses/task/{task_id}` | — | поллинг статуса анализа |
| GET | `/analyses/dream/{dream_id}` | — | `DreamPage` (загрузить готовый анализ) |

### Messages (чат с Oneiros)
| Метод | Путь | Тело | Где |
|---|---|---|---|
| POST | `/messages` | `{dream_id, content}` | `DreamPage` (отправка) |
| GET | `/messages/dream/{dream_id}?limit&offset` | — | загрузка истории |
| GET | `/messages/task/{task_id}` | — | поллинг ответа Oneiros |

### Map
| Метод | Путь | Параметры | Где |
|---|---|---|---|
| GET | `/map/{user_id}` | `?n_neighbors&min_dist&cluster_method&force_refresh` (все опциональные) | `MapPage` |
| GET | `/map/{user_id}/symbol/{symbol_id}` | — | `MapPage` (детализация символа) |

### Stats / Billing
| Метод | Путь | Где |
|---|---|---|
| GET | `/stats/me` | `ProfilePage`, `refreshStats` |
| GET | `/billing/status` | `bootstrap` (фоном), `refreshBilling` |

### Audio
| Метод | Путь | Тело | Где |
|---|---|---|---|
| POST | `/audio/transcriptions` | `multipart/form-data: file=audio.webm, language?` | `AudioButton` (composer) |

### Контракт ответа транскрипции
`{ text, partial, segments_total, segments_ok, segments_failed }`

---

## 6. Сверка с нашим backend (`backend/api/*.py`)

**Хорошая новость: все эндпоинты, которые фронт вызывает, на нашем FastAPI существуют.** Полный мэппинг роутеров — в `backend/main.py:112-120`.

| Раздел | Покрытие | Комментарий |
|---|---|---|
| auth (10 вызовов) | ✅ полностью | бэк имеет ещё `link`, `google`, `verify-email`, `resend-verification`, `reset-password` — фронт пока их не зовёт |
| users (2 вызова) | ✅ полностью | бэк имеет также `/users/me/memory` — фронт не зовёт |
| dreams (6 вызовов) | ✅ полностью | бэк имеет легаси `POST /dreams/{id}/analyze` — фронт его не зовёт (использует `POST /analyses`) |
| analyses (3 вызова) | ✅ полностью | бэк имеет ещё `GET /analyses` и `GET /analyses/{id}` — фронт не зовёт |
| messages (3 вызова) | ✅ полностью | — |
| map (2 вызова) | ✅ полностью | — |
| stats (1 вызов) | ✅ полностью | — |
| billing | ✅ `/billing/status`, `/billing/create-payment` | `/billing/webhook` вызывается YooKassa |
| audio (1 вызов) | ✅ полностью | — |
| `/api/v1/app/version` | ✅ есть | реагирует через middleware: `X-App-Version` → 426 при несовпадении |

Маршрутных пробелов **нет**. Адаптация будет на уровне форм ответа/полей (см. §7-§8 ниже).

---

## 7. Доменные типы, которые ожидает фронт (`src/lib/types.ts`)

### `User`
```ts
{ id, email|null, is_anonymous, email_verified?,
  sub_type?: 'free'|'trial'|'pro',
  linked_providers?: string[],
  profile?: { about_me?: string, onboarding_completed?: boolean } }
```
**Внимание на рассинхрон:** при `PUT /users/me` фронт **отправляет** поле `self_description`, а **читает** из ответа `profile.about_me`. То есть бэк должен:
- принимать `self_description` (или маппить `about_me`→`self_description`)
- возвращать `profile.about_me` (даже если в БД поле зовётся иначе)
- иметь `profile.onboarding_completed`

### `Dream`
```ts
{ id, user_id, title|null, content, emoji?, comment?,
  recorded_at?, created_at, updated_at?,
  has_analysis, analysis_status: 'saved'|'analyzing'|'analyzed'|'analysis_failed',
  analysis_error_message?, gradient_color_1?, gradient_color_2? }
```
Особое: `gradient_color_1/_2` используются для подсветки карточек (`DreamCard`). Если бэк их не возвращает, карточки будут серые/дефолтные — не критично, но желательно.

### `DreamListResponse` extends `PageMeta`
```ts
{ total, page, page_size, total_pages, dreams: Dream[] }
```

### `Analysis`
```ts
{ id, dream_id, user_id, result: string|null, status,
  error_message?, created_at, completed_at?|null }
```
`result` — обычный markdown (рендерится через `react-markdown`).

### `Message`
```ts
{ id, user_id, dream_id, role: 'user'|'assistant', content, created_at }
```

### `MapNode`
```ts
{ id, symbol_name, display_label, x, y, z,
  cluster_id, cluster_label, archetype_color,
  cosine_sim_to_center, size_weight,
  occurrence_count, dream_count, last_seen_at,
  preview_text, related_archetypes: string[] }
```

### `DreamMap`
```ts
{ nodes: MapNode[], clusters: MapCluster[],
  archetype_filters: string[],
  meta: { total_nodes, total_clusters, cached, computed_with,
          cluster_method, min_nodes_required } }
```

### `SymbolDetail` extends `MapNode`
```ts
{ ...MapNode,
  related_symbols: { id, symbol_name, display_label? }[],
  occurrences: { dream_id, date, text_preview }[] }
```

### `BillingStatus`
```ts
{ sub_type: 'free'|'trial'|'pro',
  sub_expires_at: string|null,
  trial_days_left: number,
  analyses_left_this_week: number|null,
  active_subscription: { product_id, expires_at }|null }
```

### `UserStats`
```ts
{ total_dreams, streak_days,
  dreams_by_weekday: Record<string, number>,
  dreams_last_14_days: { date, count }[],
  archetypes_top: { name, count }[],
  avg_time_of_day: string|null }
```

---

## 8. Возможные несоответствия и открытые вопросы

Это список вещей, которые надо явно проверить против Pydantic-моделей в `backend/schemas/`:

1. **`User.profile.about_me` vs `self_description` (PUT body)** — фронт читает одно поле, пишет другое. Бэк должен поддержать обе стороны (или унифицировать).
2. **`Dream.gradient_color_1 / gradient_color_2`** — фронт читает; если бэк не возвращает — нужно либо добавить генерацию, либо фронт мириться с дефолтами.
3. **`Dream.analysis_status`** — фронт ждёт строго четыре значения (`saved`, `analyzing`, `analyzed`, `analysis_failed`). Проверить, что бэк не присылает что-то типа `pending` или `queued`.
4. **`POST /api/v1/messages`** — фронт ждёт ответ `{ task_id, status, user_message: Message }`. Если бэк возвращает только `{task_id}` — починить либо схему ответа, либо логику фронта.
5. **`/api/v1/auth/refresh`** — фронт ждёт `{access_token, refresh_token}` (rotation). Бэк это поддерживает? Если refresh не ротируется — фронт всё равно перезапишет тот же refresh, должно работать, но проверить тип ответа.
6. **`/api/v1/auth/anonymous`** — фронт ждёт `{access_token, refresh_token, user: User}`. Бэковая `AnonymousAuthResponse` (см. `backend/api/auth.py:151`) — сверить.
7. **`platform: "web"`** в анонимной регистрации — бэк должен принимать строку `"web"` наравне с `"ios"/"android"`.
8. **CORS** — `backend/config.py:98` имеет `cors_origins = ["*"]`. На прод-домене веба надо будет сузить до фактического origin.
9. **`X-App-Version` от веба** — сейчас прибит `0.4.2`. Бэк держит `APP_MIN_VERSION = "0.3.2"` (см. `backend/main.py:150`) — пройдёт. Но при будущих апдейтах надо вести версию веба отдельно от Flutter или вместе — решить.
10. **Длинный поллинг** — `taskStatus`/`messageTaskStatus` вызываются циклом в `DreamPage`. Шаг и максимум попыток заложены в коде страницы — проверить, что бэк не таймаутит до этого.

---

## 9. Стейт-менеджмент (`src/lib/store.ts`)

Один общий store `useApp` (Zustand). Слои:

| Слой | Поля |
|---|---|
| Auth | `user`, `bootstrapping`, `ready` |
| Settings | `theme`, `accentId`, `fontSize`, `lang` |
| Data caches | `billing`, `stats`, `dreams`, `dreamsTotal`, `dreamsLoaded` |
| UI | `paywallOpen`, `paywallReason`, `upgradeBanner`, `onboardingOpen` |
| Actions | `bootstrap`, `refreshUser`, `refreshBilling`, `refreshStats`, `loadDreams`, `addDreamToCache`, `updateDreamInCache`, `removeDreamFromCache`, `setTheme/setAccent/setFontSize/setLang`, `openPaywall/closePaywall`, `setUpgradeBanner`, `openOnboarding/closeOnboarding`, `signOut` |

`signOut` принудительно делает анонимный bootstrap (то есть веб всегда «живой», даже без логина — это by design).

В DEV-режиме store доступен из консоли: `window.__innercore.useApp`.

---

## 10. Визуальные настройки (`src/lib/settings.ts`)

- `theme: 'dark' | 'light'` (дефолт `dark`)
- `accentId: 'purple'|'teal'|'amber'|'pink'|'blue'` (дефолт `purple`, `#673AB7`)
- `fontSize: 'small'|'medium'|'large'` (масштаб 0.92 / 1.0 / 1.12 через CSS-переменную `--font-scale`)
- `lang: 'ru'|'en'` (дефолт `ru`)

Применяются как `data-theme`, `--accent`, `--accent-soft` (RGB triplet), `--font-scale`, атрибут `lang`. Шторм цветов и CSS-переменные оттуда уходят в `index.css` и Tailwind-конфиг.

---

## 11. Локализация (`src/lib/i18n.ts`)

Простая словарная функция `t(key, lang)`. Два словаря: `ru` (полный), `en` (хвост в конце файла). Fallback цепочка: `dicts[lang][key] → dicts.ru[key] → key`. Без библиотек/контекста — каждая страница вытаскивает `lang` из стора и зовёт `t('namespace.key', lang)`.

Ключи структурированы по «неймспейсам»: `app.*`, `nav.*`, `compose.*`, `dream.*`, `dreams.*`, `map.*`, `search.*`, `profile.*`, `onboarding.*`, `paywall.*`, `auth.*`, `common.*`, `symbol.*`.

---

## 12. Страницы и фичи

### DreamsPage (`/`)
- Загружает список через `loadDreams()` (page=1, page_size=100).
- Composer: текстовое поле + AudioButton + кнопка отправки → `createDream` → редирект на `/dream/:id` (после `getDream(id)` для актуального состояния).
- Лимит «5 в день» — обрабатывается на бэке (429), фронт показывает локализованную ошибку.

### DreamPage (`/dream/:id`)
- `getDream(id)`, параллельно `analysisForDream(id)` (если `has_analysis`) и `messageHistory(id, 200, 0)`.
- «Анализировать»: `startAnalysis(id)` → возврат `task_id` → поллинг `taskStatus(task_id)` (через `analysisForDream` после готовности).
- Чат: `sendMessage(dream_id, content)` → возврат `task_id` → поллинг `messageTaskStatus` → перезагрузка истории.
- Редактирование заголовка/контента/даты → `updateDream(id, patch)`.
- Удаление → `deleteDream(id)`, редирект на `/`.

### MapPage (`/map`)
- `getMap(user_id)`. Параметр `force_refresh: true` доступен кнопкой «Обновить».
- Клик по узлу → `getSymbol(user_id, symbol_id)` → панель деталей.
- Если `nodes.length < min_nodes_required` — показывает «Карта проявится, когда вы запишете и проанализируете несколько снов».

### SearchPage (`/search`)
- Переключатель `semantic | lexical`.
- `searchDreams(q, mode)` по `Enter`/debounce.

### ProfilePage (`/profile`)
- Показывает `User`, `BillingStatus`, `UserStats` (графики из `Charts.tsx`).
- Поле «О себе» → `updateMe({self_description})`.
- Темы/акценты/шрифт/язык — через `setTheme/setAccent/setFontSize/setLang`.
- Войти/Зарегистрироваться → открыть `AuthModal`.
- Выйти → `signOut()`.
- Удалить аккаунт → `deleteAccount()` + signOut.

### OnboardingModal
- Открывается из `bootstrap`, если `!profile.onboarding_completed || !profile.about_me`.
- На «Завершить»: `updateMe({self_description, onboarding_completed: true})`.

### AuthModal
- Режимы: register, login, verify-email-code, forgot-password.
- После успешного login/register — `mergeAnonymous(device_id)` (fail-soft).

### PaywallModal
- Экран выбора тарифа. Кнопка подписки создаёт YooKassa payment через `/billing/create-payment` и открывает `confirmation_url`.

---

## 13. Что фронт **не** делает (но мог бы — для информации)

- **UI для Google sign-in.** Метод `api.signInGoogle(id_token)` уже есть; не хватает только подключения Google Identity Services и кнопки в `AuthModal`/`ProfilePage`. Требует `VITE_GOOGLE_CLIENT_ID`.
- **UI для привязки провайдеров.** `api.linkProvider('google'|'apple', id_token)` уже есть; UI-кнопок в `ProfilePage` нет.
- **UI для reset-password.** `api.resetPassword(token, new_password)` уже есть; нет маршрута `/reset-password?token=…` с формой.
- **Email-верификация по ссылке** (`GET /auth/verify-email?token=`) — фронт использует только 6-значный код.
- **Apple Sign-In для веба** — требует Apple Service ID + Sign in with Apple JS SDK. На бэке всё готово (`POST /auth/link` принимает `provider='apple'`), нужен только Apple Developer config.
- Покупки/подписки — web и mobile создают YooKassa redirect payment; webhook обрабатывает backend.

---

## 14. Чек-лист для подключения к нашему бэку

1. ✅ Все маршруты на месте — никакой бэк не нужно дописывать «структурно».
2. ⚠️ Сверить Pydantic-схемы ответов с `types.ts` (особенно пункты 1, 2, 3, 4 из §8).
3. ⚠️ Прокинуть `VITE_API_BASE_URL` через `.env` (создать `frontend/.env.example`).
4. ⚠️ Проверить CORS — добавить будущий веб-origin (`https://innercore.art` или какой будет) в `backend/config.py`.
5. ⚠️ Решить версионирование: одна `APP_VERSION` для веба и Flutter, или две независимые. Сейчас бэк-середина не различает.
6. ⚠️ Удалить захардкоженный `http://89.125.77.243:8080` из `api.ts` как дефолт **до релиза** (заменить на пустую строку → forced misconfig вместо подтекания тестового IP).
7. ✅ `localStorage` ключи (`innercore.*`) изолированы — конфликта с любыми другими сайтами нет.

---

Дата составления: 2026-05-27. Источник: `frontend/` в HEAD коммита `1f25510`.
