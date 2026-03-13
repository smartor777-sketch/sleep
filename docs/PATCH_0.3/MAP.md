# ТЗ — Dream Map: плоская карта символических сущностей
**Проект:** JungCore | **Версия:** 3.0 | **Стек:** FastAPI + Flutter

---

## 1. Обзор и цель

Dream Map визуализирует не сырые чанки сна и не отдельные токены, а **symbol entities** пользователя в плоском бесшовном 2D-пространстве.

Это именно карта:
- с pan и zoom
- с циклической прокруткой по X и Y
- с ручным обновлением
- с полными фильтрами по архетипам
- с переходом от symbol entity к связанным снам

Главная продуктовая идея:
- **retrieval layer** остаётся chunk-based
- **visual layer** становится symbol-entity-based
- **semantic overlay layer** строится на archetypes

---

## 2. Почему мы отказались от chunk map

Карта чанков плохо читается пользователем.

Проблемы chunk map:
- на карте появляются обрывки фраз
- подписи выглядят как случайные куски речи
- визуально это похоже не на символику сна, а на техническую отладку retrieval
- пользователь не получает ощущение “ландшафта образов”

Примеры плохих подписей:
- `того чтобы`
- `потом кстати`
- `единственное что`
- `где`
- `чуть`

Это не символика сна.

Поэтому:
- chunk остаётся внутренней единицей retrieval
- но chunk не должен быть основной UI-единицей карты

---

## 3. Что отображает карта

### 3.1 Основная видимая сущность

Основной node карты: **symbol entity**

Примеры:
- `тёмный лес`
- `чёрная вода`
- `старый дом`
- `женская фигура`
- `пустой коридор`
- `поезд в темноте`

Symbol entity:
- человекочитаема
- отражает образ
- подходит для прямого отображения на карте

### 3.2 Что не должно отображаться как node

На карте не должны отображаться:
- сырые chunk-фразы
- raw tokens
- служебные слова
- местоимения
- случайные глаголы
- разговорные обрывки

Примеры запрещённых node labels:
- `где`
- `чуть`
- `того`
- `сон`
- `находит`

### 3.3 Archetype layer

Archetypes не являются единственной меткой кластера и не должны сводиться к одному доминирующему label.

Archetypes используются как:
- фильтры
- semantic overlay
- cluster naming
- secondary metadata для symbol entities

---

## 4. Архитектурная модель

### 4.1 Три слоя

#### A. Retrieval layer

Основан на chunk'ах:
- сон режется на semantic chunks
- для chunk'ов считаются embeddings
- retrieval ищет похожие chunks

#### B. Visual layer

Основан на symbol entities:
- LLM извлекает символические сущности из сна
- symbol entities становятся узлами карты
- карта строится по ним, а не по chunk text

#### C. Semantic overlay layer

Основан на archetypes:
- archetypes связываются с symbol entities
- archetypes формируют фильтры и области
- archetypes помогают читать карту как символическое поле

---

## 5. Data flow

```text
Пользователь сохраняет сон
    ↓
Raw dream сохраняется в БД
    ↓
Chunking
    ↓
Embeddings для chunk'ов
    ↓
LLM extraction:
    - analysis_text
    - title
    - gradient
    - archetypes_delta
    - symbol_entities
    ↓
Persist:
    - dream_chunks
    - raw symbols
    - symbol_entities
    - dream_archetypes
    ↓
Map build:
    - агрегировать symbol_entities по пользователю
    - координаты symbol nodes считать по source chunks
    - archetype filters строить по всем связанным archetypes
    ↓
Redis cache
    ↓
Flutter Dream Map
```

---

## 6. LLM extraction — обязательное изменение

### 6.1 Почему нужен LLM

Новый embedding не решает проблему плохих символов.

Embedding отвечает за:
- расположение объектов в пространстве
- семантическую близость

Embedding не отвечает за:
- извлечение юнгианской символики
- превращение мусорного токена в осмысленный образ

Следовательно:
- extraction symbol entities должен делать LLM
- retrieval/positioning может оставаться на embeddings

### 6.2 Что должен возвращать LLM

После анализа сна LLM должен возвращать не только raw symbols, но и **symbol_entities**.

Минимальный JSON:

```json
{
  "analysis_text": "...",
  "title": "...",
  "gradient": {
    "color1": "#112233",
    "color2": "#445566"
  },
  "archetypes_delta": {
    "Тень": 1,
    "Самость": 1
  },
  "symbol_entities": [
    {
      "canonical_name": "лес",
      "display_label": "тёмный лес",
      "entity_type": "place",
      "weight": 0.92,
      "source_chunk_indexes": [0, 2],
      "related_archetypes": ["Тень"]
    },
    {
      "canonical_name": "вода",
      "display_label": "чёрная вода",
      "entity_type": "symbol",
      "weight": 0.88,
      "source_chunk_indexes": [1],
      "related_archetypes": ["Самость", "Тень"]
    }
  ]
}
```

### 6.3 Ограничения для LLM

LLM должен соблюдать:
- `display_label` = 1-3 слова
- label должен быть человекочитаемым
- label должен описывать образ
- нельзя возвращать местоимения
- нельзя возвращать служебные слова
- нельзя возвращать случайные разговорные куски
- нельзя подменять образ аналитическим выводом

Плохие ответы:
- `того`
- `где`
- `чуть`
- `есть`
- `находит`

Хорошие ответы:
- `старый дом`
- `чёрная вода`
- `тёмный лес`
- `женская фигура`
- `каменный мост`

---

## 7. Backend model

### 7.1 Dreams

Обычная запись сна:
- `id`
- `user_id`
- `title`
- `content`
- `analysis_text`
- `created_at`
- `updated_at`
- `gradient_color_1`
- `gradient_color_2`

### 7.2 DreamChunks

Внутренний retrieval layer:
- `id`
- `dream_id`
- `user_id`
- `chunk_index`
- `text`
- `embedding`
- `created_at`
- `metadata_json`

Назначение:
- semantic retrieval
- source grounding
- source for symbol positioning

### 7.3 DreamSymbols

Raw symbol layer:
- `id`
- `user_id`
- `dream_id`
- `chunk_id`
- `symbol_name`
- `weight`
- `created_at`

Назначение:
- нормализованный словарь символов
- overlap between chunks
- базовый retrieval overlap

### 7.4 DreamSymbolEntities

Новая сущность для карты и человекочитаемого UI.

Поля:
- `id`
- `user_id`
- `dream_id`
- `chunk_id` nullable
- `canonical_name`
- `display_label`
- `entity_type`
- `weight`
- `created_at`

Опционально:
- `source_chunk_indexes`
- `related_archetypes_json`

Пример:
- `canonical_name = вода`
- `display_label = чёрная вода`
- `entity_type = symbol`

Назначение:
- symbol nodes for Dream Map
- readable detail sheets
- связь между chunk memory и UI

### 7.5 DreamArchetypes

Связь архетипов со сном:
- `id`
- `user_id`
- `dream_id`
- `archetype_name`
- `delta`
- `created_at`

---

## 8. API карты

### 8.1 `GET /api/v1/map/{user_id}`

Возвращает symbol map.

**Query params**
- `n_neighbors`
- `min_dist`
- `cluster_method`
- `force_refresh`

**Node**
- `id`
- `symbol_name`
- `display_label`
- `x`
- `y`
- `z`
- `cluster_id`
- `cluster_label`
- `archetype_color`
- `cosine_sim_to_center`
- `size_weight`
- `occurrence_count`
- `dream_count`
- `last_seen_at`
- `preview_text`
- `related_archetypes`

**Cluster**
- `id`
- `label`
- `color`
- `count`
- `center`

**Top-level**
- `nodes`
- `clusters`
- `archetype_filters`
- `meta`

### 8.2 `GET /api/v1/map/{user_id}/symbol/{symbol_id}`

Возвращает детали symbol entity:
- `symbol_name`
- `display_label`
- `primary_dream_id`
- `cluster_label`
- `occurrence_count`
- `dream_count`
- `last_seen_at`
- `related_archetypes`
- `related_symbols`
- `occurrences`

### 8.3 `WebSocket /api/v1/map/{user_id}/stream`

Опциональный потоковый режим для больших карт.

Батчи должны передавать уже symbol nodes, а не chunks.

---

## 9. Как строится карта

### 9.1 Координаты

Координаты symbol entity вычисляются по source chunks:
- берутся embeddings связанных chunk'ов
- агрегируются в один symbol embedding
- затем выполняется редукция `1536D -> 3D`
- `x, y` идут в карту
- `z` используется как интенсивность цвета

### 9.2 Размер

Размер symbol node:
- зависит от `weight`
- частоты появления
- или `dream_count / occurrence_count`

### 9.3 Цвет

Цвет symbol node:
- зависит от `z`
- может модифицироваться archetype color

### 9.4 Chunk layer остаётся скрытым

Chunks:
- не отображаются напрямую на карте
- используются как grounding
- используются в detail/debug
- используются для вычисления символического слоя

---

## 10. Archetype filters

### 10.1 Главное правило

Фильтры не должны строиться только по доминирующему cluster label.

Это ошибка, потому что:
- тогда пользователь видит только один архетип
- карта теряет многослойность
- symbol entities с несколькими archetypes становятся невидимыми как сложные объекты

### 10.2 Правильная логика

`archetype_filters` должны содержать **полный набор archetypes**, реально связанных с symbol entities пользователя.

То есть:
- backend собирает union всех `related_archetypes` по nodes
- frontend показывает этот список как chips/filters

### 10.3 Поведение фильтра

Если выбран архетип `Тень`:
- на карте остаются все symbol entities,
- у которых `related_archetypes` содержит `Тень`

Важно:
- `cluster_label` и `archetype_filter` — разные сущности
- `cluster_label` описывает область
- `archetype_filter` фильтрует всю карту по semantic relation

---

## 11. Frontend

### 11.1 Экран

`DreamMapScreen`

Состав:
- `MapHud`
- `ArchetypeFilterBar`
- `DreamMapViewport`
- `SymbolDetailSheet`

### 11.2 Поведение

Жесты:
- drag
- pinch zoom
- tap on symbol node
- tap outside to dismiss selection

### 11.3 Бесшовная карта

Карта должна быть тороидальной:
- вышел вправо → продолжаешь слева
- вышел вверх → продолжаешь снизу

Клиент рендерит:
- центральную плитку
- соседние 8 копий

Backend хранит только одну плитку `[0..1] × [0..1]`.

### 11.4 Ручное обновление

Карта не обязана пересчитываться автоматически при каждом открытии.

Правильный UX:
- по умолчанию показывается последняя готовая версия карты
- пользователь видит кнопку `Обновить`
- при ручном обновлении карта сообщает, что идёт пересчёт
- пока пересчёт идёт, можно продолжать показывать предыдущую версию

---

## 12. Detail sheet

При tap на symbol node открывается detail sheet:
- `display_label`
- canonical symbol
- последнее появление
- количество вхождений
- количество снов
- связанные archetypes
- связанные symbols
- список последних снов/фрагментов
- CTA `Открыть сон`

Detail sheet не должен показывать бессмысленный raw token как главный заголовок.

---

## 13. Нефункциональные требования

### 13.1 Кеш

Redis cache обязателен.

Важно:
- при изменении схемы map response нужно менять cache version/prefix
- иначе старый cache может стать несовместимым с новой pydantic schema

Рекомендуется:
- versioned cache key, например `dream-map:v2`

### 13.2 Производительность

Цели:
- cached map response < 50 ms
- cold rebuild для разумного числа nodes < 2.5 s
- pan/zoom должен быть плавным на реальном устройстве

### 13.3 Идемпотентность

Повторный processing pipeline:
- не должен дублировать symbol entities
- не должен дублировать archetype links

---

## 14. Этапы реализации

### Этап 1

Hotfix / стабилизация:
- versioned map cache
- полные archetype filters
- убрать raw-token мусор из current map response

### Этап 2

Новый structured output LLM:
- добавить `symbol_entities`
- задать жёсткие правила качества label'ов

### Этап 3

Persistence:
- таблица / storage для `DreamSymbolEntities`
- связь с chunks и dreams

### Этап 4

Symbol map:
- backend map projection строится уже по persisted symbol entities
- detail sheet полностью основан на symbol entities

### Этап 5

Polish:
- archetype regions
- better halos
- heatmaps
- compare periods

---

## 15. Acceptance criteria

Dream Map считается реализованной по новой концепции, если:

1. Карта отображает symbol entities, а не сырые chunk text.
2. На карте не появляются бессмысленные токены вроде `того`, `где`, `чуть`, `сон`.
3. Каждый node карты имеет человекочитаемый label в 1-3 слова.
4. Координаты symbol nodes строятся на основе source chunks.
5. Chunk layer остаётся retrieval foundation, но не является главным visual layer.
6. В фильтрах отображается полный набор archetypes из map data.
7. Фильтр по archetype работает по `related_archetypes`, а не только по `cluster_label`.
8. Карта поддерживает бесшовную циклическую прокрутку.
9. Пользователь может вручную обновить карту и понимает, что именно обновляется.
10. Detail sheet symbol node позволяет перейти к связанному сну.

---

## 16. Итоговое решение

Dream Map — это:
- плоская 2D-карта
- бесшовная
- построенная на существующей chunk-based RAG памяти
- но визуально отображающая **symbol entities**
- с archetypes как отдельным полным semantic filter layer

Формула системы:

- `chunks` = retrieval foundation
- `symbol_entities` = visual language of the map
- `archetypes` = semantic structure and filters

Это и есть целевой продуктовый вид Dream Map.
