# JungAI — PATCH 0.4 SPEC (Implementation Plan)

Версия: 2.0
Статус: финальная спецификация
Дата: 2026-03-22
Область: `client` + `backend` + `llm_service`

---

## 0. Контекст

`PATCH_0.4/PROBLEMS.md` фиксирует идеи и болевые точки.
Этот документ — исполнимый план: что уже есть в коде, что отсутствует, какие изменения вносим, в каком порядке и как проверяем результат.

Ключевой вывод после аудита кода:

- В проекте уже есть базис для 0.4: RAG-chunks, symbol entities, карта, STT endpoint.
- Большинство требований 0.4 пока не реализованы.
- Реально завершённые части из 0.4 на сегодня:
  - `append` после повторной диктовки в записи сна (`main_chat_screen.dart`);
  - map/retrieval-слой уже symbol-entity based (наследие 0.3), но без новых требований по дисперсии и zoom x10.

Инфраструктурное решение: в проект внедряется **Alembic** для управления миграциями БД.

---

## 1. Gap-анализ по `PROBLEMS.md`

## 1.1 Голосовой ввод (длинные записи)

Что есть сейчас:

- Запись в `client/lib/screens/main_chat_screen.dart`:
  - одна локальная запись через `record`;
  - ручной старт/стоп;
  - после STT текст добавляется в поле (`append` уже реализован).
- Транскрипция:
  - `client/lib/services/transcription_service.dart` -> `POST /api/v1/audio/transcriptions`;
  - `backend/api/audio.py` и `backend/services/transcription_service.py` отправляют весь файл одним запросом в CometAPI.
- Retry/fallback по сегментам отсутствуют.
- Частичный результат при частичном фейле отсутствует.
- В `analysis_chat_screen.dart` кнопка микрофона не подключена (`onPressed: () {}`).

Разрыв с 0.4:

- Нет скрытого чанкирования.
- Нет устойчивого пайплайна для длинных записей с частичным восстановлением.
- Нет голосового ввода в чате по сну.

План:

1. Реализовать серверное сегментирование аудио (скрытое для пользователя):
   - новый модуль `backend/services/audio_chunking_service.py`;
   - decode входного файла через `pydub` (`ffmpeg` уже в Docker);
   - нарезка на сегменты **фиксированно 15 секунд**;
   - экспорт сегментов в формат оригинала (m4a/wav) во временные файлы.
2. Параллельная отправка сегментов в STT:
   - `asyncio.gather()` с `asyncio.Semaphore(3)` (до 3 параллельных запросов к CometAPI);
   - retry per segment на transient-ошибках (`429`, `5xx`, network): 3 попытки с exponential backoff.
3. Агрегация результата:
   - склейка успешных сегментов в единый текст **в порядке исходных индексов**;
   - при частичном фейле возвращать частичный текст и метаданные (`partial=true`, `failed_segments`);
   - при полном фейле всех сегментов — HTTP 503.
4. Расширить response schema `TranscriptionResponse`:
   - `text: str`
   - `partial: bool = false`
   - `segments_total: int`
   - `segments_ok: int`
   - `segments_failed: int`
5. Добавить `pydub` в `backend/requirements.txt`.
6. Клиент main chat:
   - оставить текущий UX "одна запись";
   - добавить **мягкое предупреждение** при достижении 60 сек (snackbar/toast "Запись идёт уже минуту");
   - **не останавливать запись** — пользователь может продолжать сколько хочет;
   - показать понятный статус при частичной транскрипции.
7. Клиент analysis chat:
   - вынести общую логику записи/транскрипции в `client/lib/services/voice_input_service.dart` (shared service, не mixin);
   - подключить микрофон в `analysis_chat_screen.dart` идентично main chat;
   - переиспользовать voice service в обоих экранах.

Файлы для создания:
- `backend/services/audio_chunking_service.py`
- `client/lib/services/voice_input_service.dart`

Файлы для изменения:
- `backend/services/transcription_service.py`
- `backend/api/audio.py`
- `backend/schemas/audio.py`
- `backend/requirements.txt`
- `client/lib/screens/main_chat_screen.dart`
- `client/lib/screens/analysis_chat_screen.dart`
- `client/lib/services/transcription_service.dart`

---

## 1.2 `user.md` (долгосрочная память)

Что есть сейчас:

- Есть `self_description` пользователя (`users.self_description`), ручное поле профиля.
- Есть retrieval-контекст из прошлых снов (`build_retrieval_context`), но это не эволюционный документ.
- Нет сущности `user.md`, нет пайплайна обновления после анализа.
- LLM не читает отдельную долговременную memory-сущность.

Текущий контекст анализа: `system_prompt + user.self_description + dream_text`.
Целевой контекст анализа: `system_prompt + user.self_description + user_memory_md + dream_text`.

Разрыв с 0.4:

- Полностью отсутствует механизм "оперативной карты психики" как отдельного документа.

### Ключевое решение: обновление user.md ВСТРОЕНО в анализ

Обновление user.md происходит **при каждом анализе сна** (не по эвристике "значимости").
Отдельная Celery-задача для обновления user.md **НЕ нужна**.

Механизм:
1. `analyze_dream_task` передаёт текущий `user_memory_md` в LLM вместе с dream_text.
2. Основной analysis prompt расширяется: LLM возвращает в JSON-ответе дополнительное поле `memory_update`.
3. `memory_update` — это **diff-объект** с операциями над секциями user.md:
   ```json
   {
     "memory_update": {
       "recurring": {"action": "replace", "value": "control / chaos / water"},
       "archetypes": {"action": "replace", "value": "shadow (growing), anima (emerging)"},
       "emotional_shift": {"action": "replace", "value": "anxiety -> exploration -> acceptance"},
       "phase": {"action": "replace", "value": "integration"}
     }
   }
   ```
4. Backend применяет diff к `user_memory_docs` после успешного анализа.
5. При первом анализе (user.md ещё нет) — LLM получает пустой `user_memory_md: ""`, создаёт документ с нуля.

### Фиксированные 4 секции user.md

```markdown
## recurring
control / chaos

## archetypes
shadow (growing)

## emotional_shift
anxiety -> exploration

## phase
transition
```

LLM не может добавлять свои секции. Только обновлять существующие 4.

План:

1. Добавить хранилище памяти:
   - новая таблица `user_memory_docs` (Alembic-миграция):
     - `id UUID PK`
     - `user_id UUID UNIQUE FK`
     - `content_md TEXT NOT NULL DEFAULT ''`
     - `version INT NOT NULL DEFAULT 1`
     - `updated_at TIMESTAMPTZ NOT NULL`
   - поле `last_source` убрано — обновление всегда при анализе.
2. Добавить сервис `backend/services/user_memory_service.py`:
   - `get_or_create(user_id) -> UserMemoryDoc`
   - `apply_memory_update(user_id, memory_update_dict, current_version) -> UserMemoryDoc`
   - optimistic concurrency: `WHERE version = current_version`, retry 1 раз при конфликте.
3. Расширить `analyze_dream_task`:
   - перед вызовом LLM: загрузить текущий `user_memory_md`;
   - передать `user_memory_md` в llm_client;
   - после получения JSON-ответа: извлечь `memory_update`, применить через `user_memory_service`.
4. Расширить LLM-контракт:
   - llm_service `/analyze` принимает `user_memory_md` (optional string);
   - llm_service `/chat` принимает `user_memory_md` (optional string, read-only — чат не обновляет memory);
   - analysis prompt требует вернуть `memory_update` в JSON-ответе.
5. Добавить debug endpoint:
   - `GET /api/v1/users/me/memory` (только текущий пользователь).

Файлы для создания:
- `backend/services/user_memory_service.py`
- `backend/models/user_memory.py`
- Alembic-миграция для `user_memory_docs`

Файлы для изменения:
- `backend/tasks.py` (analyze_dream_task + reply_to_dream_chat_task)
- `backend/services/llm_client.py` (добавить user_memory_md в вызовы)
- `llm_service/main.py` (принять user_memory_md)
- `llm_service/prompts.py` (расширить analysis prompt, добавить memory_update в JSON-схему)
- `backend/prompts.py` (расширить chat system prompt, включить user.md как контекст)
- `backend/api/users.py` или новый файл для debug endpoint

---

## 1.3 Карта символов и архетипов (дисперсия + zoom x10)

Что есть сейчас:

- `backend/services/map_service.py` уже строит карту по symbol entities (не по raw chunks).
- Есть UMAP/PCA + DBSCAN/fallback, archetype filters.
- Клиент карты (`dream_map_screen.dart`) ограничивает zoom: `0.7..3.0`.
- Pan ограничен рамкой (bounded), не toroidal (это соответствует финальному решению 0.3).

Разрыв с 0.4:

- Недостаточная дисперсия и слабые пересечения между снами.
- Нет zoom x10.
- Нет отдельного режима "глобального позиционирования + controlled noise".

План:

1. Улучшить layout-алгоритм карты (backend):
   - L2-нормализация векторов symbol entities перед редукцией;
   - настройка UMAP под большую межкластерную дисперсию (`min_dist` выше текущего default);
   - deterministic jitter на node-координаты:
     - seed: `hashlib.md5(f"{user_id}:{symbol_name}".encode()).hexdigest()[:8]` → int seed;
     - амплитуда: **3% от диапазона координат** (range_x, range_y);
     - воспроизводимость: одни и те же координаты при одних и тех же данных.
2. Ввести версионирование layout:
   - `meta.layout_version = "v4"`;
   - cache-prefix поднять до `dream-map:v4`.
3. Добавить управляемые параметры (API query, с разумными default):
   - `dispersion` (0..1, default 0.5);
   - `jitter` (0..1, default 0.3).
4. Клиент карты:
   - увеличить clamp zoom до `0.5..10.0`;
   - адаптировать рендер labels/halos под большие zoom;
   - LOD: при zoom < 2x — только крупные узлы (weight > median), при zoom > 5x — все узлы + мелкие labels.

Важно:

- bounded-pan из 0.3 сохраняем.
- Меняется плотность/структура пространства, а не навигационная модель.

Файлы для изменения:
- `backend/services/map_service.py`
- `client/lib/screens/dream_map_screen.dart`
- `backend/api/map.py` (или где определён endpoint карты)

---

## 1.4 Временная динамика данных

Что есть сейчас:

- В `DreamChunk` есть `created_at`, но это технический timestamp записи chunk в БД.
- Retrieval использует `dream.created_at` только как дату в prompt-блоке.
- Явного temporal score, временной оси и timestamp per chunk для анализа динамики нет.
- Текущая формула retrieval: `hybrid_score = embedding_score + (0.18 * symbol_overlap) + (0.12 * archetype_overlap)`.

Разрыв с 0.4:

- Нет явной временной модели для chunks.
- LLM не получает структурированный временной контекст "прошлое -> настоящее".

План:

1. Расширить модель `dream_chunks` (Alembic-миграция):
   - `source_recorded_at TIMESTAMPTZ NOT NULL` (время сна, из `dream.recorded_at`);
   - `source_created_at TIMESTAMPTZ NOT NULL` (исторический `dream.created_at`);
   - `source_order INT NOT NULL` (дублирует `chunk_index` для явной семантики порядка).
2. В `rebuild_dream_memory` заполнять новые поля для каждого chunk.
3. Миграция/бэкфилл (Alembic data migration):
   - для старых chunk-строк заполнить `source_recorded_at/source_created_at` через join с `dreams`;
   - `source_order` = `chunk_index`.
4. Добавить temporal scoring в retrieval:
   - формула: `hybrid_score = embedding_score + (0.18 * symbol_overlap) + (0.12 * archetype_overlap) + recency_bonus`;
   - `recency_bonus = 0.1 * exp(-days_ago / 30)` — мягкий бонус свежим снам, полупериод ~30 дней;
   - не вытесняет semantic similarity, а мягко приоритизирует recent + recurring.
5. Расширить prompt-block (`RetrievalContext.to_prompt_block`):
   - передавать дату+время (`YYYY-MM-DD HH:mm`);
   - явно маркировать последовательность по времени.
6. Обновить analyze/chat prompts:
   - требование сравнивать прошлое и настоящее;
   - выделять динамику изменений и циклы.

Файлы для создания:
- Alembic-миграция для новых полей `dream_chunks`
- Alembic data-миграция для бэкфилла

Файлы для изменения:
- `backend/models/rag.py` (DreamChunk)
- `backend/services/rag_service.py` (rebuild_dream_memory, build_retrieval_context, RetrievalContext.to_prompt_block)
- `llm_service/prompts.py` (temporal instructions)
- `backend/prompts.py` (temporal instructions for chat)

---

## 2. Roadmap внедрения

## Этап A (P0): Голосовой ввод стабильно

Цель:

- Закрыть user-facing критичные проблемы: длинная запись и voice в чате.

Задачи:

1. `backend`:
   - `services/audio_chunking_service.py` — split via pydub, 15-sec segments;
   - обновить `services/transcription_service.py` — parallel STT с Semaphore(3);
   - обновить `api/audio.py` и `schemas/audio.py` — новый response schema.
2. `client`:
   - `services/voice_input_service.dart` — shared voice recording + transcription service;
   - подключить в `analysis_chat_screen.dart`;
   - мягкое предупреждение при 60 сек в обоих экранах (без hard stop).
3. Тесты:
   - backend unit: full success, partial fail, full fail;
   - client: append behavior, analysis chat mic flow.

Гейт этапа:

- AC 1,2,3 из `PROBLEMS.md` выполняются.

---

## Этап B (P1): `user.md` как долговременная память

Цель:

- Ввести эволюционный memory-документ, который обновляется при КАЖДОМ анализе сна.

Задачи:

1. Внедрить Alembic в проект (init + baseline migration).
2. Alembic-миграция: таблица `user_memory_docs`.
3. `services/user_memory_service.py` — get_or_create, apply_memory_update.
4. Расширить `analyze_dream_task`: загрузка memory → передача в LLM → применение diff.
5. Расширить llm_service `/analyze` и `/chat`: принять `user_memory_md`.
6. Расширить `llm_service/prompts.py`: analysis prompt возвращает `memory_update` в JSON.
7. Расширить `backend/prompts.py`: chat system prompt включает user.md.
8. Debug endpoint `GET /api/v1/users/me/memory`.

Гейт этапа:

- AC 4,5,6 выполняются.

---

## Этап C (P1): Временная ось chunks + temporal retrieval

Цель:

- Сделать time-awareness системным.

Задачи:

1. Alembic-миграция: новые поля `dream_chunks` + data backfill.
2. Обновление `rag_service`:
   - заполнение temporal полей в `rebuild_dream_memory`;
   - `recency_bonus` в retrieval scoring.
3. Обновление prompt контекста: timestamps в `to_prompt_block`.
4. Обновление LLM-инструкций по динамике (analyze + chat prompts).

Гейт этапа:

- AC 10,11 выполняются.

---

## Этап D (P2): Новая дисперсия карты + zoom x10

Цель:

- Улучшить читаемость межсновых пересечений.

Задачи:

1. Новый projection profile (`map_service.py`): L2-norm, UMAP min_dist, deterministic jitter + cache v4.
2. API-параметры: `dispersion`, `jitter`.
3. Клиентский zoom до x10 + LOD рендер.
4. Перф-тест на реальных данных карты.

Гейт этапа:

- AC 7,8,9 выполняются.

---

## Этап E (P1): Локализация — убрать хардкод русского текста

Цель:

- Все пользовательские строки проходят через l10n. Нет хардкода на русском в dart-файлах.

Задачи:

1. Добавить 37 ключей в `app_ru.arb` и `app_en.arb` (включая ICU-параметры для строк с `$variable`).
2. Заменить хардкод на `AppLocalizations.of(context)!.key` в 6 файлах.
3. `flutter gen-l10n` для генерации dart-кода.

Гейт этапа:

- `grep` по `client/lib/` не находит кириллических строковых литералов вне `.arb` файлов и комментариев.
- AC 12 выполняется.

---

## 1.5 Локализация: устранение хардкода русского текста

Что есть сейчас:

- Проект использует `flutter_localizations` + `.arb` файлы (`app_ru.arb`, `app_en.arb`).
- Большинство строк локализовано через `AppLocalizations.of(context)!.key`.
- Однако в **6 файлах** обнаружено **37 хардкод-строк на русском**, которые не проходят через l10n.

Полный реестр хардкода:

**`onboarding_screen.dart`** (19 строк — самый проблемный файл):
- `'Давайте познакомимся'`
- `'Шаг ${_step + 1} из $_stepCount'`
- `'Пропустить'`, `'Завершить'`, `'Далее'`
- `'Чем вы сейчас занимаетесь?'` + hint + placeholder
- `'Расскажите немного о семье...'` + hint + placeholder
- `'Какие у вас увлечения...'` + hint + placeholder
- `'Что сейчас особенно важно...'` + hint + placeholder
- `'Чтобы лучше понимать контекст ваших снов...'`
- `'Пол и возраст можно пропустить...'`
- `'Возраст'`, `'$_age лет'`
- `'Женщина'`, `'Мужчина'`, `'Предпочитает не указывать пол'`
- `'Не удалось завершить онбординг'`

**`dream_map_screen.dart`** (8 строк):
- `'Обновить'`
- `'Карта обновляется. Пока показываем предыдущую версию.'`
- `'Добавьте ещё $missingCount снов...'`, `'Карта пока недоступна.'`
- `'Символ: ...'`, `'Последнее появление: ...'`, `'N вхождений в N снах'`
- `'Архетипы'`, `'Связанные символы'`, `'Где встречается'`, `'Открыть последний сон'`

**`profile_screen.dart`** (2 строки):
- `'Сны за 14 дней'`
- `'Архетипы'`

**`main_chat_screen.dart`** (2 строки):
- `'Чат сна'`
- `'Выберите сон в плитке, чтобы открыть его анализ и чат.'`

**`analysis_chat_screen.dart`** (2 строки):
- `'Изменить дату'`
- `'Повторить анализ'`

**`widgets/message_menu.dart`** (1 строка):
- `'Изменить дату'`

План:

1. Добавить все 37 строк как ключи в `app_ru.arb` (русские значения) и `app_en.arb` (английские переводы).
2. Заменить хардкод на `AppLocalizations.of(context)!.keyName` во всех 6 файлах.
3. Для строк с параметрами (`$missingCount`, `$_age`, `$_step`) использовать ICU message format в `.arb`.
4. Запустить `flutter gen-l10n` для генерации dart-файлов.

Файлы для изменения:
- `client/lib/l10n/app_ru.arb`
- `client/lib/l10n/app_en.arb`
- `client/lib/screens/onboarding_screen.dart`
- `client/lib/screens/dream_map_screen.dart`
- `client/lib/screens/profile_screen.dart`
- `client/lib/screens/main_chat_screen.dart`
- `client/lib/screens/analysis_chat_screen.dart`
- `client/lib/widgets/message_menu.dart`

---

## 3. Изменения контрактов

## 3.1 Backend API

`POST /api/v1/audio/transcriptions`:

- Было: `{ "text": "..." }`
- Станет:

```json
{
  "text": "recognized text",
  "partial": false,
  "segments_total": 4,
  "segments_ok": 4,
  "segments_failed": 0
}
```

`GET /api/v1/users/me/memory` (NEW, debug):

```json
{
  "version": 7,
  "updated_at": "2026-03-21T12:00:00Z",
  "content_md": "## recurring\ncontrol / chaos\n\n## archetypes\nshadow (growing)\n\n## emotional_shift\nanxiety -> exploration\n\n## phase\ntransition"
}
```

## 3.2 Internal LLM contract

`llm_service /analyze` request:

```json
{
  "dream_text": "...",
  "user_description": "...",
  "user_memory_md": "## recurring\n..."
}
```

`llm_service /analyze` response расширяется:

```json
{
  "analysis_text": "...",
  "title": "...",
  "gradient": [...],
  "archetypes_delta": {...},
  "symbol_entities": [...],
  "memory_update": {
    "recurring": {"action": "replace", "value": "control / chaos / water"},
    "archetypes": {"action": "replace", "value": "shadow (growing), anima (emerging)"},
    "emotional_shift": {"action": "replace", "value": "anxiety -> exploration -> acceptance"},
    "phase": {"action": "replace", "value": "integration"}
  }
}
```

`llm_service /chat` request:

```json
{
  "messages": [...],
  "user_memory_md": "## recurring\n..."
}
```

Чат **не** возвращает `memory_update` — только анализ обновляет user.md.

---

## 4. Миграции и совместимость

Инструмент: **Alembic** (внедряется в рамках 0.4).

Порядок миграций:

1. `alembic init` + настройка `env.py` для async SQLAlchemy.
2. Baseline миграция: снапшот текущей схемы (`--autogenerate` от существующих моделей, пустая upgrade — БД уже в этом состоянии).
3. Миграция `create_user_memory_docs`: создание таблицы.
4. Миграция `add_temporal_fields_to_dream_chunks`: новые поля + data backfill через join с `dreams`.

Порядок деплоя:

1. `alembic upgrade head` (DDL + backfill).
2. Деплой llm_service с поддержкой `user_memory_md`.
3. Деплой celery worker (расширенный analyze_dream_task).
4. Деплой backend (новые endpoints + audio chunking).
5. Деплой клиента (voice in analysis chat + zoom x10).

Совместимость:

- Старые клиенты продолжат работать: расширения API backward-compatible.
- Новые поля в responses optional для старого клиента.
- `user_memory_md` optional в LLM-запросах: если не передан, поведение как раньше.

---

## 5. План тестирования

## 5.1 Backend

- `test_audio_chunking_service.py`:
  - long audio (45s) -> 3 segments x 15s;
  - short audio (10s) -> 1 segment, no split;
  - empty audio -> error.
- `test_transcription_chunking.py`:
  - multi-segment parallel success;
  - partial segment failure -> `partial=true`, text non-empty;
  - all segments fail -> 503.
- `test_user_memory_service.py`:
  - create memory for new user;
  - apply_memory_update updates content_md and increments version;
  - optimistic lock conflict -> retry succeeds.
- `test_analyze_with_memory.py`:
  - analysis returns `memory_update` in response;
  - memory_update applied to DB after analysis;
  - first analysis creates user.md from scratch.
- `test_rag_temporal.py`:
  - chunk timestamps persisted from dream;
  - recency_bonus increases score for recent chunks;
  - old chunks still appear if semantically relevant.
- `test_map_projection_v4.py`:
  - dispersion metrics above baseline;
  - deterministic jitter: same input -> same coordinates;
  - jitter amplitude within 3% of coordinate range.

## 5.2 Client

- `voice_input_service`:
  - start/stop recording;
  - transcription call + append to controller.
- `analysis_chat_screen`:
  - mic button connected and functional;
  - append transcription to message input.
- `main_chat_screen`:
  - soft warning at 60s (no hard stop);
  - partial transcription status display.
- `dream_map_screen`:
  - pinch zoom up to 10x;
  - LOD: labels hidden at low zoom, shown at high zoom;
  - tap-hit still usable at high zoom.

## 5.3 E2E

1. Записать длинный голос (>60 сек) -> получить цельный текст.
2. Повторно продиктовать -> текст дополнился.
3. В чате сна нажать микрофон -> запись/транскрипция/отправка работает.
4. Создать новый сон -> после анализа `user.md` создан/обновлён.
5. Проверить `GET /api/v1/users/me/memory` -> корректный content_md с 4 секциями.
6. На карте заметны межсновые пересечения, zoom до x10.
7. Retrieval prompt содержит timestamp chunks, отсортированные по времени.

---

## 6. Риски и меры

Риск: Рост latency STT из-за сегментации.
Мера: Параллельная обработка сегментов, `Semaphore(3)`. Для 60с аудио = 4 сегмента, 2 батча по 3 = ~2x latency одного запроса вместо 4x.

Риск: Race condition при параллельных обновлениях `user.md`.
Мера: Optimistic concurrency (`version` field) + 1 retry. Race маловероятен: user.md обновляется только при анализе, а анализ — последовательная операция per user.

Риск: Перегрузка рендера карты на x10.
Мера: LOD (level of detail) — скрытие мелких узлов/labels при низком zoom, progressive disclosure при высоком.

Риск: LLM не возвращает `memory_update` в JSON или возвращает невалидный diff.
Мера: Парсинг memory_update опционален — если поле отсутствует или невалидно, анализ проходит успешно, user.md просто не обновляется. Логируем warning.

---

## 7. Полная карта затрагиваемых файлов

### Создаваемые файлы

| Файл | Этап | Назначение |
|------|------|-----------|
| `backend/alembic/` (init) | B | Alembic infrastructure |
| `backend/alembic.ini` | B | Alembic config |
| `backend/services/audio_chunking_service.py` | A | pydub split + temp files |
| `backend/services/user_memory_service.py` | B | CRUD + apply diff для user.md |
| `backend/models/user_memory.py` | B | SQLAlchemy model UserMemoryDoc |
| `client/lib/services/voice_input_service.dart` | A | Shared voice recording service |
| Alembic migration: `create_user_memory_docs` | B | DDL |
| Alembic migration: `add_temporal_fields` | C | DDL + backfill |

### Изменяемые файлы

| Файл | Этап | Изменение |
|------|------|-----------|
| `backend/requirements.txt` | A | +pydub |
| `backend/services/transcription_service.py` | A | parallel segment STT |
| `backend/api/audio.py` | A | chunking orchestration |
| `backend/schemas/audio.py` | A | extended TranscriptionResponse |
| `backend/tasks.py` | B | user.md load/save в analyze_dream_task |
| `backend/services/llm_client.py` | B | pass user_memory_md |
| `backend/prompts.py` | B,C | chat prompt: user.md + temporal |
| `backend/models/rag.py` | C | DreamChunk temporal fields |
| `backend/services/rag_service.py` | C | temporal scoring, rebuild_dream_memory |
| `backend/services/map_service.py` | D | L2-norm, UMAP, jitter, cache v4 |
| `llm_service/main.py` | B | accept user_memory_md |
| `llm_service/prompts.py` | B,C | memory_update in JSON, temporal instructions |
| `client/lib/screens/main_chat_screen.dart` | A | use voice_input_service, 60s warning |
| `client/lib/screens/analysis_chat_screen.dart` | A | connect mic via voice_input_service |
| `client/lib/services/transcription_service.dart` | A | handle extended response |
| `client/lib/screens/dream_map_screen.dart` | D | zoom x10, LOD |
| `client/lib/l10n/app_ru.arb` | E | +37 ключей локализации |
| `client/lib/l10n/app_en.arb` | E | +37 ключей (английские переводы) |
| `client/lib/screens/onboarding_screen.dart` | E | 19 строк → l10n |
| `client/lib/screens/dream_map_screen.dart` | D,E | zoom x10, LOD + 8 строк → l10n |
| `client/lib/screens/profile_screen.dart` | E | 2 строки → l10n |
| `client/lib/screens/main_chat_screen.dart` | A,E | voice_input_service + 2 строки → l10n |
| `client/lib/screens/analysis_chat_screen.dart` | A,E | connect mic + 2 строки → l10n |
| `client/lib/widgets/message_menu.dart` | E | 1 строка → l10n |

---

## 8. Итоговое заключение

PATCH 0.4 можно внедрить без переписывания архитектуры:

- Голос: серверное чанкирование 15с + параллельный STT + partial results.
- Память: user.md обновляется при каждом анализе через diff в JSON-ответе LLM.
- Время: temporal поля в chunks + recency_bonus в retrieval scoring.
- Карта: L2-norm + UMAP tuning + deterministic jitter + zoom x10 с LOD.

Рекомендуемый порядок внедрения: `P0 Voice -> P1 user.md (+ Alembic) -> P1 Temporal -> P1 Локализация -> P2 Map`.
