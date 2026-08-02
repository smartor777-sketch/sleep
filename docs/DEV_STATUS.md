# InnerCore — статус разработки (dev-sleep-test)

Сервер: `sleep-test.kuban-forum.ru` → `2.26.51.8`
Репозиторий: `smartor777-sketch/sleep.git`, ветка `dev-sleep-test`

Последнее обновление: 2026-08-02

## Что сделано

### Билинг и доступ (все — Pro)
- `backend/services/billing_service.py` — `refresh_entitlements` форсирует `sub_type="pro"`,
  `sub_expires_at=None` для **всех** пользователей (trial-логика отключена, `has_full_access()` → `True`).
- Проверено: аноним и зарегистрированный пользователи отдают `{"sub_type":"pro"}`.

### LLM: модель и fallback
- Бенчмарк (тот же реальный запрос): `gemini-3.6-flash` 13.6с/3844 симв. vs `gemini-3.5-flash-lite`
  4.2с/3735 симв. — качество практически идентично.
- Основная модель: **`gemini-3.5-flash-lite`**; Gemini fallback-цепочка
  `["gemini-3.6-flash", "gemini-3.5-flash"]`; внешний fallback — **Mistral** (`mistral-large-latest`).
- `llm_service/config.py` — заменены `comet_api_key/comet_base_url/comet_model` на
  `mistral_api_key/mistral_base_url/mistral_model`.
- `llm_service/providers/mistral.py` (новый) — MistralProvider (OpenAI-совместимый,
  `POST https://api.mistral.ai/v1/chat/completions`, Bearer, `max_tokens=12000`).
- `llm_service/main.py` — импорт и инициализация Mistral-провайдера, логи CometAPI → Mistral.
- Серверный `.env`: `GEMINI_MODEL=gemini-3.5-flash-lite`, `MISTRAL_API_KEY=…`, `MISTRAL_MODEL=mistral-large-latest`.
- Проверено реальным анализом: запрос ушёл на `gemini-3.5-flash-lite:generateContent 200`,
  celery `succeeded in 5.78s`, статус `completed`.
- Примечание: `gemini-3.6-flash-lite` не существует (404) — не использовать.

### Аналитика и диагностика
- Celery worker активен; все analyses в БД `completed`.
- Цикл: received → Starting → POST /analyze 200 → committed → completed (17–100с).
- Долгие ответы — не RAG (эмбеддинги + pgvector 0–2с), а сам Gemini `generateContent`
  (утром 503 от Google, ретраи).

### Контекст чата LLM
- `backend/services/message_service.py`:
  - `CONTEXT_CHAR_BUDGET`: 28 000 → **400 000** символов (~100k токенов).
  - `MAX_RECENT_MESSAGES`: 20 → **50**.
  - Входной контекст `gemini-3.5-flash-lite` = 1M токенов, запас большой.

### Фронтенд: дублирование в диалоге
- `frontend/src/pages/DreamPage.tsx` — в «Диалоге о сне» больше **не дублируются** первое
  user-сообщение (текст сна) и первый assistant-ответ (полный разбор): они уже показаны
  в hero-карточке и блоке «Разбор InnerCore». В чате остаётся только follow-up переписка.
- Зафиксировано на бэкенде (`api/messages.py`) — API теперь сам скрывает первое user/assistant
  сообщение, работает даже для закешированного фронта.

### Карта снов: порог мержа + семантические рёбра
- `_SYMBOL_MERGE_THRESHOLD = 0.80` (было 0.6, под OpenAI) — задеплоено, перезапуск backend,
  кэш v5. Карта больше не схлопывается в один узел «заяц».
- Добавлены **семантические рёбра** в API карты (`schemas.map.DreamMapEdgeResponse`):
  - **co_dream** — символы из одного сна (общие dream_id), вес = число общих снов.
  - **embedding** — косинусная близость концептов ≥ 0.65 (gemini-embedding-001), вес = cosine.
- На фронте: переключатель «Связи» — **Из одного сна / По смыслу / Декоративные** (дефолт — co_dream).
- Цвет рёбер адаптивен к теме (`--map-link`): тёмный в light, светлый в dark (был невидим на light).
- Кеш префикс обновлён `dream-map:v5`.

### Тестовый пользователь
- Создан через API: `test.sleep@innercore.example.com` / `Test12345!`
- 4 сна: «Полёт над морем», «Лес и волк», «Запертая комната», «Разговор с бабушкой»
- Проанализирован 1 сон → карта строится (5 узлов). Остальные запускать вручную.

### Иконки (прод)
- В коде используются только `/icon.png`, `/icon-background.png` (+ favicon из index.html).
- Залиты в `/srv/sleep-test-web/frontend/dist/`: `favicon.png`, `favicon.svg`, `icon.png`,
  `icon-background.png`. HTTP 200, `icon.png` = 468 558 байт.
- При деплое фронта не забывать заливать эти 4 файла вместе с `assets/`.

## Исправлено
- Дублирование разбора InnerCore в «Диалоге о сне» — убрано (фронт + бэк).
- `llm_service/main.py` побился по UTF-8 от PowerShell `Set-Content` — восстановлен
  `git checkout --`, правки применены заново через редактор. Правило: python-файлы
  с кириллицей править только редактором, не `Set-Content`.

## Коммиты
- `ca0a9ea` — Pro для всех пользователей.
- `a106bfa` — переключение на gemini-3.5-flash-lite + Mistral fallback.
- `de4acf8` — увеличение контекстного бюджета чата (~100k токенов).
- `3c42419` — убрано дублирование в диалоге (фронт + бэк API).
- `e56a5cc` — поднят порог мержа символов до 0.80 (gemini-embedding-001).
- `6e2ead0` — семантические рёбра карты (co_dream + embedding) + переключатель режимов + адаптивный цвет.

## Next Move
1. Проверить карту в UI (Ctrl+F5) — узлы + рёбра должны отображаться в обеих темах.
2. При деплое фронта заливать 4 иконки + assets.
3. Запускать анализ остальных тестовых снов для насыщения карты.

## Серверные заметки
- SSH: `plink -ssh -batch -pw "yO3aN0cU6efK" root@2.26.51.8 "…"`; upload — `pscp.exe -batch -pw …`.
- systemd: `innercore-backend`, `innercore-celery`, `innercore-llm`
  (конфиг `/srv/sleep-test/llm_service/.env`).
- PostgreSQL: `PGPASSWORD=inn3rc0re_dev_2026 psql -U innercore -h 127.0.0.1 -d innercore`.
- curl с Windows требует `-k` к `https://sleep-test.kuban-forum.ru` (сертификат не проверяется
  с этой машины); с сервера всё отвечает 200.
- Временные скрипты на сервере: `compare_models.py`, `show_results.py`, `check_map.py`,
  `check_chunks.py`, `debug_map.py`, `test_emb.py`, `test_syn.py`, `add_dream.py`,
  `trigger_analysis2.py`, `check_edges_api.py`.