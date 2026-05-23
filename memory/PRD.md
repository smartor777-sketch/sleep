# InnerCore Web — PRD & build log

## Исходная задача
Сделать веб-SPA-фронтенд InnerCore с паритетом к существующему мобильному Flutter-клиенту.
Бэкенд (FastAPI) уже существует — фронт обращается к нему по HTTP API. Объём первой итерации:
**только SPA, без лендинга**. Аутентификация — только анонимная для MVP.

## Стек
- React 18 + Vite + TypeScript
- Tailwind CSS (тёмная/светлая темы, 5 акцентов: фиолетовый/teal/янтарь/розовый/синий)
- React Router v6, Zustand (state), axios, react-markdown, lucide-react
- Запуск: `yarn start` (vite на 0.0.0.0:3000) под supervisor

## Архитектура и контракт с бэкендом
- `VITE_API_BASE_URL` (по умолч. `http://89.125.77.243:8080`) — внешний URL бэкенда.
- Все запросы шлют `X-App-Version: 0.4.2`.
- `Authorization: Bearer <jwt>`, авто-refresh при 401 (single-flight).
- Хранение: `device_id`, `access_token`, `refresh_token` в `localStorage`.
- Маршруты: `/`, `/dream/:id`, `/map`, `/search`, `/profile`.

## Веб-адаптация UI (после итерации 2)
- **Layout современного AI-SaaS**: постоянный левый sidebar (272px) + sticky topbar.
- **Sidebar**: бренд-лого с фирменным градиентом, крупный pill-CTA «Новый сон» (⌘N) с shortcut hint,
  workspace-секция с навигацией (icon-pill каждая, активный пункт = вертикальный accent-bar +
  тонированная подсветка пилюли), снизу — plan-widget с аватаром, тарифом и кнопкой апгрейда.
- **Topbar**: page-title + subtitle, theme-toggle, аватар-линк на профиль. На /dream/:id показывает
  back-arrow вместо гамбургера. Глобальный 426-баннер встроен сверху.
- **Mobile (lg-)**: sidebar превращается в drawer (slide-in слева), открывается гамбургером;
  оверлей + Esc для закрытия.
- **Композер**: крупный textarea-блок с поэтическим placeholder, char-counter, audio-кнопкой,
  send-pill и подсказкой шортката ⌘↵.
- **Грид снов**: auto-fill minmax(220px, 1fr) — на 1440px ≈5 колонок, на 1024 — 4, на 768 — 3,
  на мобиле — 2; нет растяжения карточек.

### Прокси-шлюз (dev convenience)
`/app/backend/server.py` — простой httpx-proxy. Пробрасывает `/api/*` на внешний backend, чтобы
preview-домен (HTTPS) мог демонстрироваться с HTTP-бэкендом, обходя Mixed Content/CORS.
Управляется через env `UPSTREAM_API`.

## Что реализовано
- **Bootstrap**: device_id → анонимный вход → проверка профиля → онбординг при необходимости.
- **Главный экран** `/`: сетка карточек снов (адаптивная 2/3/4 колонки), компоновщик с микрофоном
  (MediaRecorder → `POST /api/v1/audio/transcriptions` → текст в поле), нижняя навигация.
- **Карточки снов**: фирменный градиент `#FA9042 → #8885FF` по умолчанию, дата, заголовок
  (первые 3 слова, если не задан), значки статуса анализа.
- **Экран сна** `/dream/:id`: hero-карточка с градиентом, текст, кнопка «Анализировать»
  (`POST /analyses`, polling 2с), Markdown-разбор, чат с polling ответов (gate для FREE → Paywall).
- **Карта снов** `/map`: REST `GET /map/{user_id}`, кружки-узлы с цветами архетипов, мягкие свечения
  кластеров, фильтры архетипов, pan + zoom (1×–5×), деталь символа (нижний sheet) с `related_symbols`/
  `occurrences`. FREE-юзер → premium-гейт.
- **Поиск** `/search`: semantic/lexical с debounce 350мс.
- **Профиль** `/profile`: «о себе» (`PUT /users/me`), тариф (`/billing/status`), статистика
  (`/stats/me`): всего, стрик, бар-чарт 14 дней, top архетипы. Настройки: тема (тёмная/светлая),
  акцент (5 цветов), размер шрифта (small/medium/large), язык (RU/EN). Регистрация/вход + verify
  по 6-значному коду + merge анонимных данных, удаление аккаунта.
- **Paywall** (заглушка): триггерится на 402 при анализе, на чат/карту для FREE.
- **426 Upgrade Required**: глобальный баннер сверху.
- **i18n** RU/EN (полный словарь).
- **data-testid** на всех ключевых элементах.

## Ограничения текущего окружения
- Из preview-домена upstream `http://89.125.77.243:8080` отдаёт reset на POST-запросы
  (вероятно, IP-фильтр на write-операции). GET `/health` и `/api/v1/app/version` работают.
- Поэтому в preview не получится завершить флоу анонимного входа end-to-end.
- На локальном бэкенде у вас всё заработает: либо настройте `VITE_API_BASE_URL` напрямую,
  либо используйте прокси через `UPSTREAM_API=http://localhost:8000`.

## Структура файлов
```
/app/frontend/
├── package.json, vite.config.ts, tsconfig.json, tailwind.config.js, postcss.config.js
├── .env                       # VITE_API_BASE_URL, VITE_APP_VERSION
├── index.html
├── public/favicon.svg
└── src/
    ├── main.tsx, App.tsx, index.css
    ├── lib/
    │   ├── api.ts             # axios + X-App-Version + auto-refresh + все эндпоинты
    │   ├── store.ts           # zustand: user, billing, dreams cache, UI state
    │   ├── settings.ts        # theme/accent/font/lang persistence
    │   ├── i18n.ts            # RU+EN
    │   └── types.ts           # Dream/Analysis/Message/MapNode/...
    ├── components/
    │   ├── Layout.tsx, Splash.tsx, Modal.tsx
    │   ├── DreamCard.tsx, Markdown.tsx, AudioButton.tsx
    │   ├── PaywallModal.tsx, OnboardingModal.tsx, AuthModal.tsx
    └── pages/
        ├── DreamsPage.tsx     # /
        ├── DreamPage.tsx      # /dream/:id
        ├── MapPage.tsx        # /map
        ├── SearchPage.tsx     # /search
        └── ProfilePage.tsx    # /profile

/app/backend/server.py         # httpx proxy → UPSTREAM_API
```

## Чеклист паритета (Definition of Done из спеки)
- [x] Анонимный старт по device_id, `X-App-Version` на всех запросах
- [x] Авто-refresh токенов при 401
- [x] Email регистрация/вход + 6-значный код + сброс пароля
- [x] Merge анонимных данных при первом входе
- [x] CRUD снов: создание (429 → toast), список, поиск (semantic/lexical)
- [x] Дефолтный заголовок (3 слова) и градиент `#FA9042→#8885FF`
- [x] Ручной запуск анализа кнопкой, polling прогресса, Markdown-результат
- [x] Title/градиент обновляются после анализа (через перечитывание dream)
- [x] Чат: отправка, polling, история, Markdown, gate для FREE
- [x] Карта снов: узлы/кластеры/фильтры/деталь символа/refresh
- [x] Статистика профиля (стрик, 14-дневный график, топ архетипов)
- [x] Голосовой ввод → транскрипция → текст в поле сна
- [x] `billing/status` → Paywall-заглушка
- [x] Локализация RU + EN
- [x] Обработка 426 (баннер)
- [ ] Google Sign-In (отложено по запросу пользователя)

## Что отложено / следующие шаги
- Google Sign-In через GIS (web client id)
- Прогрессивная WebSocket-загрузка карты (`/map/{user_id}/stream`)
- Реальная оплата (ЮKassa/Stripe) — сейчас заглушка
- Лендинг (отдельная задача)
- E2E-тестирование с настоящим бэкендом (не получилось в preview-окружении из-за IP-фильтра upstream)
