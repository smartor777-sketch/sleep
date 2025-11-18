Отлично — у тебя очень чёткая продуктовая идея. Ниже — полное ТЗ (техническое задание) для мобильного клиента JungAI (Flutter). Я описал экраны, поведение, модели данных, архитектуру состояния, связь с бэкендом, не забыв про UX-нюансы (поиск, календарь, long-press меню, голосовой ввод) и нефункциональные требования (безопасность, офлайн, тесты). Ты просил без примеров кода, поэтому только спецификация и логика.

⸻

1. Цель

Создать минималистичный мобильный клиент JungAI для iOS и Android. Основной сценарий — пользователь быстро записывает сны в чат-ленту и при необходимости запускает AI-анализ (отдельная ветка). Интерфейс простой и быстрый, похож на чат — минимум полей при создании сна.

⸻

2. Основные принципы UX
	•	Минимализм: одно поле ввода, переключение текст/голос, возможность прикрепить изображение.
	•	Низкий порог входа: нет дополнительных обязательных полей (title, emoji и т.д.) — всё как в мессенджере.
	•	Быстрая навигация: поиск и календарь как иконки в header, открывающие панели поверх ленты (не уводя со страницы).
	•	Контекстные действия через long-press с блюром фона.
	•	Анализ сна — отдельный чат/ветка, уникален для каждого сна (один анализ на сон).
	•	Без лишних подтверждений: запись отправляется мгновенно, редактирование — в контекстном режиме.

⸻

3. Список экранов и модулей (high-level)
	1.	Onboarding / Auth
	•	Login (email/password)
	•	Register (email/password)
	•	Email verification / password reset — минимально видимые элементы, всё через бэкенд
	2.	Main Chat (Dream List / Feed) — главный экран
	•	Header: название, кнопки Поиск и Календарь, Menu/Profile
	•	Контент: непрерывная лента снов (сообщения), пагинация/ленивая подгрузка
	•	Floating input panel: переключатель Text/Voice, поле ввода, Attach Image, Send
	•	Long-press context menu (копировать / редактировать / удалить / анализировать)
	3.	Analysis Chat (ветка по сну)
	•	Первый сообщения: исходный текст сна (от пользователя)
	•	Второй: результат LLM (появляется после завершения задачи)
	•	Дальше: свободный диалог с LLM (как чат)
	•	Статус анализа (processing, ready, failed)
	4.	Search Panel (вкладка/overlay в header)
	•	Поле ввода запроса
	•	Быстрые результаты с превью (фрагмент текста + дата)
	•	По тапу — скролл к месту и временная подсветка сообщения
	5.	Calendar Panel
	•	Календарь (выбор даты)
	•	При выборе даты — результаты/фильтр (скролл к первому сообщению выбранного дня)
	6.	Profile / Settings
	•	Поле “About me” (свободный текст)
	•	Статистика: total dreams, streak (дни подряд), записи по дням недели/часам (визуализация)
	•	Настройки (выход, уведомления, экспорт данных)
	7.	Image picker / Attachment UI
	•	Поддержка выбора из галереи и камеры
	•	Маленький превью прикреплённого изображения в сообщении
	8.	Error / Empty / Loading states
	•	Empty feed, offline indicator, loader при запросах, toasts/snackbars для ошибок

⸻

4. Навигация и UX-поведение
	•	Навигация: single activity (или single navigator) — Main Chat как root. Анализ открывается как отдельный экран (push), profile и настройки — modal / push.
	•	Поиск и Календарь: иконки в header. Нажатие раскрывает overlay (panel) поверх ленты, лента остаётся видимой: overlay занимает верхнюю часть экрана; закрывается повторным нажатием/свайпом вниз.
	•	Скролл к результату: по тапу в результатах поиска/календаря происходит плавный scrollTo указанного сообщения с временной подсветкой (flash highlight 1s).
	•	Long-press: вызывает context menu прямо над сообщением; фон — размытая и затемнённая лента (псевдо-blur). Menu items: Copy, Edit, Delete, Analyze. При выборе Delete — подтверждение (undo via snackbar).
	•	Отправка сна: мгновенная отправка. Если офлайн или ошибка сети — сообщение помечается как unsent (retry). Голосовое распознавание — локально: текст появляется в поле ввода, пользователь может отредактировать и нажать Send.
	•	Анализ: при нажатии Analyze запрос создаётся асинхронно (Celery). UI сразу открывает комнату анализа: показывает “processing” + индикатор. Через вебхук/polling/GET task API — когда результат готов, он появляется как сообщение LLM. После этого пользователь может продолжать диалог.

⸻

5. Модель данных (клиентская модель / JSON-шаблоны)

Ниже — рекомендованные поля; они должны соответствовать / дополнять бэкенд-контракты.

Dream (сообщение/сон)

dream {
  id: string (uuid),
  user_id: string,
  content: string,           // основной текст сна
  created_at: ISO8601,
  updated_at: ISO8601 | null,
  attachments: [ attachment ], // 0..n (картинки)
  local_state: enum { synced, pending, failed } // клиентская
}

Attachment

attachment {
  id: string,
  url: string | null,      // если загружено в MinIO
  mime_type: string,
  local_path: string | null // если временно в клиенте
}

AnalysisTask / AnalysisChat

analysis {
  id: string,               // task id
  dream_id: string,
  status: enum { pending, processing, ready, failed },
  created_at: ISO8601,
  result: [ message ] | null,
}

Message (within analysis chat)

message {
  id: string,
  sender: enum { user, ai },
  content: string,
  created_at: ISO8601
}

UserProfile

profile {
  id: string,
  email: string,
  about_me: string,   // свободный текст
  created_at: ISO8601
}

Stats (computed on client or from backend)

stats {
  total_dreams: integer,
  streak_days: integer,
  dreams_by_weekday: { Mon: n, Tue: n, ... },
  avg_time_of_day: string, // можно хранить расчет
}


⸻

6. API интеграция (логика взаимодействия, mapping, ожидания)

(опираемся на твой backend: /api/v1/auth, /api/v1/dreams, /api/v1/analyses)

Аутентификация
	•	Логин/регистрация возвращают JWT access/refresh.
	•	Клиент хранит access в flutter_secure_storage.
	•	Каждый запрос к приватным endpoint добавляет Authorization: Bearer <token>.

Dreams
	•	GET /api/v1/dreams?limit=&offset=&query=&date= — список (пагинация, фильтр по тексту/дате).
	•	POST /api/v1/dreams — тело: { content: string, attachments?: [] } — создаёт сон.
	•	PUT /api/v1/dreams/{id} — редактирование.
	•	DELETE /api/v1/dreams/{id} — удаление.
	•	POST /api/v1/dreams/{id}/attachments — загрузка изображения (multipart).

Клиент: при отправке нового сна — сначала создать локально (local_id), показать в ленте с state pending, затем отправить запрос. При успехе — заменить local_id на server id, state → synced. При ошибке — show retry.

Analyses
	•	POST /api/v1/analyses — запрос на анализ { dream_id } → возвращает task_id.
	•	GET /api/v1/analyses/task/{task_id} — статус task.
	•	GET /api/v1/analyses/dream/{dream_id} — если анализ уже готов, получить историю/чат.

Поведение: если GET /analyses/dream/{dream_id} показывает, что анализ существует — кнопку Analyze скрывать/дисейблить (так как только один анализ на сон).

Search / Calendar
	•	Search: использовать GET /api/v1/dreams?q=... (или искать уже загруженные на клиенте). Для простоты MVP: делать локальный поиск по уже загруженным сообщениям + backend search при необходимости.
	•	Calendar: GET /api/v1/dreams?date=YYYY-MM-DD — или фильтрация локально.

⸻

7. State management и архитектура клиента

Рекомендация (MVP)
	•	Provider / ChangeNotifier или Riverpod — для простоты MVP Provider с четким разделением:
	•	AuthProvider — хранит токены, профиль, авторизованное состояние.
	•	DreamsProvider — хранит список сообщений, пагинацию, методы create/update/delete, локальные состояния.
	•	AnalysisProvider — хранит активные/архивные анализы, методы создания таска и polling.
	•	ProfileProvider — профиль и статистика.

Структура слоёв
	•	UI (screens, widgets)
	•	State (providers)
	•	Services:
	•	ApiService — HTTP wrapper с retry, backoff, token refresh.
	•	StorageService — secure storage (JWT), local DB/cache (sqflite/hive) для офлайна.
	•	MediaService — работа с изображениями (resize, compress), загрузка.
	•	SpeechService — локальное speech-to-text (платформенно: iOS Speech API / Android SpeechRecognizer).
	•	SyncService — управление очередью отправки (outbox), retry, reconciliation.

Offline & Persistence
	•	Использовать лёгкую локальную БД (Hive или sqflite) для кеша сообщений и офлайн режима.
	•	Outbox pattern: если пользователь пишет при офлайне — сообщение добавляется в локальную очередь и отправляется при восстановлении сети.
	•	Local copy должна сохранять timestamps, attachments (temp files), and send status.

⸻

8. Голосовой ввод (Speech-to-Text)
	•	MVP: использовать платформенные возможности (iOS Speech API, Android SpeechRecognizer) — локальное распознавание.
	•	Поведение:
	•	Кнопка Microphone переключает режим ввода: нажал — начинается запись, распознавание в реальном времени → текст вставляется в поле ввода.
	•	При нажатии Send — отправляется распознанный текст.
	•	UI: индикатор записи, cancel, auto stop on silence.
	•	Права: запрос разрешения на микрофон.

⸻

9. Загрузка картинок (attachments)
	•	При прикреплении изображение предварительно сжимается/thumbnail создаётся (чтобы экономить трафик).
	•	Отправка: multipart upload к POST /dreams/{id}/attachments или предварительный запрос на получение одноразового upload URL (S3/MinIO).
	•	Пока attachment не загружен — сообщение помечается attachment_pending; отображать placeholder.
	•	В профиле/просмотре — возможность открыть изображение fullscreen.

⸻

10. Ограничения и бизнес-логика
	•	Ограничение: 5 снов в день — клиент обязан отображать ошибку/состояние ограничения (backend возвращает 429 или структурированную ошибку). В UI — показать объяснение и время сброса (например, “Вы достигли лимита — следующий доступ через X часов”).
	•	Анализ: только один анализ на сон — при попытке запросить второй анализ — показать подсказку/disabled button.
	•	Rate limiting: клиент должен аккуратно обрабатывать 429 и применять exponential backoff.
	•	Безопасность: хранить JWT в secure storage; для refresh использовать refresh token flow; очистка при logout.

⸻

11. UI-детали / микро-взаимодействия
	•	Input panel:
	•	Left: toggle Text/Voice (icon), Center: multiline TextField auto-expand (max 5 lines), Right: Attach (paperclip), Send (floating button).
	•	При входе в поле ввода — клавиатура поднимает чат, последняя запись видна.
	•	Message bubble:
	•	Однострочный / многострочный, дата над/под сообщением.
	•	Внизу каждой bubble — небольшой индикатор статуса (pending, failed, synced).
	•	Long press menu:
	•	Появляется contextual card с blur background.
	•	Элементы: Copy (clipboard), Edit (in-place modal with text field), Delete (confirmation), Analyze (if allowed).
	•	Analysis chat:
	•	Слева/справа разделение: пользователь / AI.
	•	При первом открытии show “Analysis in progress…” + spinner until ready.
	•	Profile stats:
	•	KPI блоки (total dreams, streak) + горизонтальная/вертикальная мини-диаграмма (weekday heatmap) — простые бар/column chart (можно реализовать later).

⸻

12. События, логика и последовательности (flows)

Создание сна (нормальный поток)
	1.	User types or records voice → filled text.
	2.	User taps Send.
	3.	Client creates local Dream (local_id), shows in feed with pending.
	4.	Client attempts POST /dreams.
	•	On success: update id/state.
	•	On error: set failed and offer Retry.

Редактирование сна
	1.	Long-press → Edit.
	2.	User edits → Save → PUT /dreams/{id}.
	3.	Update local and server; handle conflicts (last write wins or show merge prompt).

Удаление сна
	1.	Long-press → Delete → Confirm.
	2.	Client deletes local item (optimistic) and calls DELETE /dreams/{id}.
	3.	Provide undo via snackbar during short window.

Анализ сна
	1.	Long-press → Analyze → Client POST /analyses → receives task_id.
	2.	Open Analysis Chat — show pending.
	3.	Poll GET /analyses/task/{task_id} или backend отправляет push/websocket update.
	4.	When ready — fetch chat content GET /analyses/dream/{dream_id} and show LLM result as AI message.
	5.	After that — user can continue conversation (POST messages to analysis chat backed by same LLM pipeline).

⸻

13. Notifications / Real-time
	•	MVP: polling for analysis task (paired with reasonable interval/backoff).
	•	Опционально: later — WebSocket / Push notifications (для уведомления о завершении анализа).

⸻

14. Тестирование и качество
	•	Unit tests: провайдеры, services (mock ApiService).
	•	Widget tests: Main Chat input, message bubble, context menu.
	•	Integration tests: full login → create dream → analyze → receive result.
	•	Manual QA: offline mode, large attachments, network flakiness, 5 dreams/day limit.

⸻

15. CI / Deployment (кратко)
	•	Настроить CI: Flutter analyze, tests, build for iOS (macos runner) and Android (linux runner).
	•	Artifacts: Android debug/apk, iOS xcarchive for TestFlight.
	•	При релизе: интеграция с backend (env variables) и secrets (YANDEX key не в мобилке — LLM вызовы идут через backend).

⸻

16. Безопасность и конфиденциальность
	•	Хранить JWT в secure storage; refresh token flow handled by backend.
	•	Не хранить YandexGPT keys в мобильном клиенте.
	•	Для экспортов (PDF/JSON) — делать на бэкенде.
	•	При сборе статистики/telemetry — спросить разрешение (opt-in).
	•	Защита данных: предусмотреть экспорт/удаление аккаунта (через backend).

⸻

17. Нефункциональные требования
	•	Поддержка оффлайн: чтение локального кеша, запись в outbox.
	•	Плавный UX: скроллы, подсветка, анимации минималистичны.
	•	Размер клиента: оптимизировать изображения перед загрузкой.
	•	Доступность: large fonts, contrast.

⸻

18. Мерки, оценки и итерации (roadmap для разработки)

Рекомендую разбить на итерации:

Итерация 0 (Setup)
	•	Настроить проект, providers, ApiService, secure storage.
	•	Basic auth flow.

Итерация 1 (Core chat)
	•	Main chat UI, input panel (text), send dream, list/pagination, long-press menu (copy/edit/delete).
	•	Local persistence basic (Hive/sqflite).

Итерация 2 (Search / Calendar)
	•	Search overlay, calendar overlay, scrollTo, highlight.

Итерация 3 (Attachments + Voice)
	•	Image attach + upload, voice recognition integration (iOS/Android).

Итерация 4 (Analysis)
	•	Analysis task creation, polling, analysis chat UI.

Итерация 5 (Profile & Stats)
	•	About me, stats calculation and UI.

Итерация 6 (Polish & QA)
	•	Error handling, offline polish, tests, CI.

