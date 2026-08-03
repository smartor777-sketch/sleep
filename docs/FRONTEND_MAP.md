# FRONTEND_MAP.md — карта веб-клиента `frontend/`

Снимок состояния после коммита `78a2ab8`.
Тестовый сервер: `sleep-test.kuban-forum.ru`.

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
| Дев-сервер | `vite --host 0.0.0.0 --port 3000`, `strictPort: true`, `hmr.clientPort: 443` |
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
| `/admin` | `AdminPage` — админ-панель (только для admin) |
| `*` | редирект на `/` |

Поверх маршрутов: `<OnboardingModal />`, `<PaywallModal />`, `<AuthModal />` (вызывается из `ProfilePage`).

---

## 3. Конфигурация и env-переменные

Vite читает `import.meta.env`. Используются:

| Переменная | Дефолт | Зачем |
|---|---|---|
| `VITE_API_BASE_URL` | `https://sleep-test.kuban-forum.ru` | Базовый URL бэкенда |
| `VITE_APP_VERSION` | `0.4.2` | Уходит в `X-App-Version` на каждом запросе |

---

## 4. API-клиент (`src/lib/api.ts`)

### Базовое поведение
- Каждый запрос несёт заголовок `X-App-Version: <VITE_APP_VERSION>`.
- JWT в `Authorization: Bearer <access_token>`, кроме запросов с `__skipAuth: true` в config (login/register/anon/refresh/verify/resend/forgot).
- На `401` — единственная попытка `tryRefresh()` (single-flight), повтор оригинала; при провале — `clearTokens()` + `onForceLogout()`.
- На `426 Upgrade Required` — вызывает `onUpgradeRequired(info)`.
- Все ошибки оборачиваются в `ApiError { status, data, detail }`.

### LocalStorage-ключи
| Ключ | Значение |
|---|---|
| `innercore.device_id` | UUID устройства |
| `innercore.access_token` | JWT access |
| `innercore.refresh_token` | JWT refresh |
| `innercore.settings.v1` | JSON `{theme, accentId, fontSize, lang}` |

---

## 5. Эндпоинты, которые ждёт фронт

### Auth
| Метод | Путь | Описание |
|---|---|---|
| POST | `/auth/anonymous` | Анонимная авторизация |
| POST | `/auth/register` | Регистрация (email + password) |
| POST | `/auth/login` | Вход (email + password) |
| POST | `/auth/refresh` | Обновление токена |
| GET | `/auth/email-mode` | Публичный: `{"email_auth_enabled": bool}` |
| POST | `/auth/verify-email-code` | Верификация 6-значного кода |
| POST | `/auth/resend-code` | Повторная отправка кода |
| POST | `/auth/merge-anonymous` | Мерж анонимных снов после логина |
| DELETE | `/auth/account` | Удаление аккаунта (самостоятельно) |

### Admin (требует `is_admin`)
| Метод | Путь | Описание |
|---|---|---|
| GET | `/admin/stats` | Агрегированная статистика |
| GET | `/admin/users` | Список пользователей (поиск, пагинация) |
| POST | `/admin/users` | Создание пользователя |
| PATCH | `/admin/users/{id}` | Обновление полей (is_active, is_admin, name) |
| POST | `/admin/users/{id}/reset-password` | Сброс пароля |
| DELETE | `/admin/users/{id}` | Удаление пользователя (каскад) |
| GET | `/admin/settings/email-auth` | Текущий режим email-auth |
| PUT | `/admin/settings/email-auth` | Переключение режима email-auth |

### Users
| Метод | Путь | Описание |
|---|---|---|
| GET | `/users/me` | Текущий пользователь |
| PUT | `/users/me` | Обновление профиля |

### Dreams
| Метод | Путь | Описание |
|---|---|---|
| POST | `/dreams` | Создать сон |
| GET | `/dreams` | Список снов (пагинация) |
| GET | `/dreams/search` | Поиск (semantic/lexical) |
| GET | `/dreams/{id}` | Карточка сна |
| PATCH | `/dreams/{id}` | Редактирование |
| DELETE | `/dreams/{id}` | Удаление |

### Analyses
| Метод | Путь | Описание |
|---|---|---|
| POST | `/analyses` | Запуск анализа |
| GET | `/analyses/task/{task_id}` | Статус задачи |
| GET | `/analyses/dream/{dream_id}` | Готовый анализ |

### Messages (чат с Oneiros)
| Метод | Путь | Описание |
|---|---|---|
| POST | `/messages` | Отправить сообщение |
| GET | `/messages/dream/{dream_id}` | История чата |
| GET | `/messages/task/{task_id}` | Статус ответа |

### Map
| Метод | Путь | Описание |
|---|---|---|
| GET | `/map/{user_id}` | Карта символов |
| GET | `/map/{user_id}/symbol/{symbol_id}` | Детализация символа |

### Stats / Billing
| Метод | Путь | Описание |
|---|---|---|
| GET | `/stats/me` | Статистика пользователя |
| GET | `/billing/status` | Статус подписки |

### Audio
| Метод | Путь | Описание |
|---|---|---|
| POST | `/audio/transcriptions` | Транскрипция аудио |

---

## 6. Стейт-менеджмент (`src/lib/store.ts`)

Один общий store `useApp` (Zustand). Слои:

| Слой | Поля |
|---|---|
| Auth | `user`, `bootstrapping`, `ready` |
| Settings | `theme`, `accentId`, `fontSize`, `lang` |
| Data caches | `billing`, `stats`, `dreams`, `dreamsTotal`, `dreamsLoaded` |
| UI | `paywallOpen`, `paywallReason`, `upgradeBanner`, `onboardingOpen` |
| Actions | `bootstrap`, `refreshUser`, `refreshBilling`, `refreshStats`, `loadDreams`, `addDreamToCache`, `updateDreamInCache`, `removeDreamFromCache`, `setTheme/setAccent/setFontSize/setLang`, `openPaywall/closePaywall`, `setUpgradeBanner`, `openOnboarding/closeOnboarding`, `signOut` |

---

## 7. Страницы и фичи

### AuthModal
- Режимы: `register` (Регистрация) / `login` (Вход).
- **Email-only**: нет кнопок соцсетей.
- После успешного register: проверяет `emailMode()` → если `email_auth_enabled=true` → показывает шаг ввода 6-значного кода, иначе сразу в аккаунт.
- После login/register → `mergeAnonymous(device_id)` (fail-soft).

### AdminPage (`/admin`)
- Статистика (юзеры, сны, анализы, анонимы, premium, актив за 7д).
- Создание пользователей (email + пароль + имя).
- Таблица пользователей: имя, email, сны, подписка, статус, действия.
- Действия: сброс пароля, toggle admin, toggle block, **удаление**.
- Удаление: красная кнопка → модальное окно «Все данные будут удалены безвозвратно» → подтверждение.
- Email-auth toggle: включение/выключение режима кода.
- Нельзя удалить/заблокировать самого себя.

### DreamsPage (`/`)
- Composer: текст + AudioButton → `createDream` → редирект на `/dream/:id`.

### DreamPage (`/dream/:id`)
- Анализ: `startAnalysis(id)` → поллинг `taskStatus`.
- Чат: `sendMessage` → поллинг `messageTaskStatus` → перезагрузка истории.
- Редактирование, удаление.

### MapPage (`/map`)
- `getMap(user_id)`. Клик по узлу → `getSymbol(user_id, symbol_id)`.

### SearchPage (`/search`)
- Переключатель `semantic | lexical`. Поиск по `Enter`.

### ProfilePage (`/profile`)
- Профиль, биллинг, настройки темы/шрифта/языка.
- Войти/Зарегистрироваться → открыть `AuthModal`.
- Удалить аккаунт → `deleteAccount()` + signOut.

### OnboardingModal
- Открывается из `bootstrap`, если `!profile.onboarding_completed || !about_me`.

### PaywallModal
- Выбор тарифа. YooKassa redirect payment.

---

## 8. Визуальные настройки (`src/lib/settings.ts`)

- `theme: 'dark' | 'light'` (дефолт `dark`)
- `accentId: 'purple'|'teal'|'amber'|'pink'|'blue'` (дефолт `purple`)
- `fontSize: 'small'|'medium'|'large'` (масштаб 0.92 / 1.0 / 1.12)
- `lang: 'ru'|'en'` (дефолт `ru`)

---

## 9. Локализация (`src/lib/i18n.ts`)

Простая словарная функция `t(key, lang)`. Два словаря: `ru` (полный), `en`. Fallback: `dicts[lang][key] → dicts.ru[key] → key`.

Ключи: `app.*`, `nav.*`, `compose.*`, `dream.*`, `dreams.*`, `map.*`, `search.*`, `profile.*`, `onboarding.*`, `paywall.*`, `auth.*`, `common.*`, `symbol.*`.

---

## 10. Иконки

В коде используются: `/icon.png`, `/icon-background.png` (+ `favicon.png` из `index.html`).
Директория: `/srv/sleep-test-web/frontend/dist/`.

---

Дата составления: 2026-08-03. Источник: `frontend/` в HEAD коммита `78a2ab8`.
