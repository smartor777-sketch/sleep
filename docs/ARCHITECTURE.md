# Архитектура проекта InnerCore

## Обзор

InnerCore — платформа для анализа снов с использованием ИИ. Пользователи записывают сны, система автоматически анализирует их, извлекает символы, выявляет паттерны и строит интерактивную «Карту снов».

---

## Стек технологий

| Компонент | Технология |
|-----------|-----------|
| Frontend | React 19 + TypeScript + Vite + Tailwind CSS |
| Backend | Python 3.12 + FastAPI + SQLAlchemy (async) + Alembic |
| БД | PostgreSQL 16 + pgvector |
| Кэш | Redis |
| Очередь задач | Celery + Redis broker |
| LLM | Google Gemini (chat + embeddings) |
| Деплой | systemd + Caddy reverse proxy |

---

## Архитектура бэкенда

### Структура каталогов

```
backend/
├── main.py              # FastAPI app, startup/shutdown, middleware
├── config.py            # Pydantic Settings (env vars)
├── database.py          # async SQLAlchemy engine, init_db(), Alembic migrations
├── models/              # SQLAlchemy ORM-модели
│   ├── user.py          # User, UserOAuth, UserSubscription
│   ├── dream.py         # Dream (сырые тексты снов)
│   ├── rag.py           # DreamChunk + pgvector embedding_vec
│   ├── symbols.py       # DreamSymbol (символы, извлечённые из снов)
│   └── analysis.py      # DreamAnalysis, AnalysisSummary, AnalysisSymbols
├── schemas/             # Pydantic response/request модели
├── api/                 # Router-эндпоинты
│   ├── auth.py          # /auth/login, /register, /verify-email-code
│   ├── dreams.py        # CRUD снов
│   ├── admin.py         # /admin/* (статистика, управление юзерами)
│   ├── map.py           # /map/* (карта снов: узлы, рёбра, кластеры)
│   └── rag.py           # /rag/* (RAG-эндпоинты)
├── services/            # Бизнес-логика
│   ├── dream_service.py # Анализ снов, семантический поиск
│   ├── rag_service.py   # RAG-память: retrieval context для LLM
│   ├── map_service.py   # Построение карты: кластеризация, визуализация
│   ├── embedding_service.py  # Вызов Gemini Embedding API, cosine similarity
│   ├── settings_service.py   # Админ-настройки (email-auth toggle)
│   └── symbol_service.py     # Извлечение символов из снов
├── tasks.py             # Celery-задачи (async анализ снов)
├── alembic/             # Миграции БД
│   └── versions/
│       └── 002_pgvector_rag.py  # Векторный индекс
└── requirements.txt
```

---

## Система эмбеддингов и векторный поиск

### Модель эмбеддингов

- **Модель**: Google Gemini `gemini-embedding-001`
- **Размерность**: 768
- **Провайдер**: Google AI API (через API-ключ в `GOOGLE_API_KEY`)

Эмбеддинги используются для:
1. **RAG-памяти** — поиск похожих фрагментов прошлых снов
2. **Карты снов** — позиционирование символов в 2D/3D пространстве
3. **Семантического поиска** — поиск снов по запросу пользователя

### Хранение эмбеддингов

Эмбеддинги хранятся в **двух форматах** одновременно:

| Колонка | Таблица | Тип | Формат | Используется |
|---------|---------|-----|--------|-------------|
| `embedding_vec` | `dream_chunks` | `vector(768)` | pgvector binary | RAG (HNSW ANN-поиск) |
| `embedding_text` | `dream_chunks` | `TEXT` | JSON-массив float | Карта снов (Python cosine) |
| `embedding_text` | `dreams` | `TEXT` | JSON-массив float | Семантический поиск снов |

**Почему два формата**: pgvector-колонка нужна для HNSW-индекса (O(log N) поиск), но map_service работает с данными в JSON-формате (концепт-эмбеддинги, попарные сравнения), где pgvector не даёт преимуществ.

### HNSW-индекс

```sql
-- Миграция 002_pgvector_rag.py
CREATE EXTENSION IF NOT EXISTS vector;

ALTER TABLE dream_chunks ADD COLUMN embedding_vec vector(768);

CREATE INDEX ix_dream_chunks_embedding_vec
  ON dream_chunks USING hnsw (embedding_vec vector_cosine_ops);
```

**Тип индекса**: HNSW (Hierarchical Navigable Small World) — O(log N) поиск ближайших соседей по cosine distance.

**Используется в**: `rag_service.py` — при анализе нового сна ищет топ-40 самых похожих фрагментов прошлых снов.

### Поток данных эмбеддингов

```
Текст сна → Chunking (макс 320 символов)
           → Gemini Embedding API (768d)
           → dream_chunks.embedding_vec  (pgvector)  → RAG-ретривал
           → dream_chunks.embedding_text (JSON)      → Карта снов

Текст сна (целиком) → Gemini Embedding API (768d)
                    → dreams.embedding_text (JSON)   → Семантический поиск снов
```

---

## RAG-память (Semantic Memory)

### Назначение

При анализе каждого нового сна LLM получает контекст из похожих фрагментов прошлых снов пользователя. Это позволяет системе замечать повторяющиеся темы, паттерны и связи.

### Поток анализа

1. **Чанкинг**: текст сна разбивается на семантические фрагменты (макс. 320 символов)
2. **Эмбеддинг**: каждый чанк встраивается через Gemini API
3. **Хранение**: эмбеддинги сохраняются в `dream_chunks` (vector + JSON)
4. **Ретривал**: HNSW-поиск находит топ-40 кандидатов по cosine distance
5. **Пере-ранжирование**: гибридный скор =
   - `embedding_score` (cosine similarity) × 1.0
   - `symbol_overlap` × 0.18
   - `archetype_overlap` × 0.12
   - `recency_bonus` (новизна)
6. **Инъекция в промпт**: топ-6 чанков → «SEMANTIC MEMORY CONTEXT» в системном промпте LLM

### Fallback

Если pgvector недоступен (extension не установлена, ошибка), система автоматически переключается на **Python cosine similarity** по JSON-эмбеддингам — полный O(N) скан по `dream_chunks.embedding_text`.

---

## Карта снов (Dream Map)

### Назначение

Интерактивная 2D/3D-визуализация символов снов пользователя. Семантически похожие символы расположены ближе друг к другу.

### Построение карты

#### 1. Извлечение символов

Символы извлекаются из каждого сна LLM: объекты, существа, эмоции, места, действия. Каждый символ сохраняется в `dream_symbols` с привязкой к сну.

#### 2. Концепт-эмбеддинги

Для каждого уникального символа вычисляется **концепт-эмбеддинг** — эмбеддинг текстовой подписи символа (например, «чёрная вода»). Результат кешируется в Redis (`concept-emb:v1:*`) с TTL 7 дней.

**Почему не pgvector**: концепт-эмбеддинги — это одиночные векторы для позиционирования нод. Их мало (обычно 20-100), и pgvector не даёт преимуществ для таких объёмов.

#### 3. Слияние синонимов

Близкие по смыслу символы объединяются в одну ноду:

```python
# embedding_service.py
greedy_cosine_cluster(labels, threshold=0.80)
```

Алгоритм: однопроходный greedy clustering, порог cosine similarity = 0.80. Например, «озеро» и «озеро с островами» сливаются в одну ноду.

#### 4. Проекция в 2D

Матрица эмбеддингов символов проецируется в 2D:
- **Основной метод**: UMAP (cosine metric)
- **Fallback**: PCA (если sklearn/umap недоступны)

#### 5. Кластеризация

DBSCAN кластеризует 2D-точки:
- `eps` рассчитывается автоматически на основе плотности
- `min_samples` = max(2, min(5, N/10))
- Каждый кластер получает метку доминирующего архетипа (Jung)

#### 6. Рёбра между символами

Два типа связей:

| Тип | Описание | Порог | Вес |
|-----|----------|-------|-----|
| `co_dream` | Символы в одном сне | — | Кол-во общих снов |
| `embedding` | Семантическое сходство | cosine >= 0.65 | Значение cosine |

### Качество кластеров

Для каждого узла вычисляется `cosine_sim_to_center` — cosine similarity между эмбеддингом ноды и средним эмбеддингом кластера. Метрика отображается в UI как `size_weight`.

---

## Семантический поиск снов

Пользователь вводит запрос → система находит наиболее релевантные сны:

1. Запрос встраивается через Gemini API
2. Загружаются сны пользователя (до limit×4 для фильтрации)
3. Для каждого сна вычисляется cosine similarity с запросом (JSON-эмбеддинг, Python)
4. Возвращаются топ-N снов по релевантности

**Почему не pgvector**: таблица `dreams` не имеет vector-колонки (только JSON `embedding_text`). Добавление pgvector для `dreams` возможно, но пока нецелесообразно — сон целиком rarely превышает 10K, и O(N) scan быстр.

---

## Утилита cosine similarity

Вся система использует единую функцию:

```python
# embedding_service.py
def cosine_similarity(a: list[float], b: list[float]) -> float:
    dot = float(sum(x * y for x, y in zip(a, b)))
    norm_a = sum(x * x for x in a) ** 0.5
    norm_b = sum(y * y for y in b) ** 0.5
    return dot / (norm_a * norm_b)
```

**Где используется**:
- `rag_service.py` — fallback-ретривал и пере-ранжирование
- `map_service.py` — рёбра, кластер-центр, слияние синонимов
- `dream_service.py` — семантический поиск снов
- `embedding_service.py` — greedy_cosine_cluster

---

## Почему архитектура работает так, а не иначе

| Задача | Решение | Почему не альтернатива |
|--------|---------|----------------------|
| RAG: поиск 40 кандидатов из 10K+ чанков | pgvector HNSW (O(log N)) | Python O(N) scan слишком медленный |
| Карта: позиционирование 20-100 нод | UMAP/PCA + Python cosine | pgvector не нужен — мало данных |
| Карта: слияние синонимов (N×N попарно) | greedy_cosine_cluster (Python) | pgvector не поддерживает попарные операции |
| Карта: рёбра (N×N попарно) | cosine_similarity (Python) | pgvector ANN не для попарных сравнений |
| Поиск снов (100-500 снов) | Python cosine (JSON scan) | pgvector для `dreams` таблицы не добавлен |

**Правило**: pgvector используется когда нужен ANN-поиск по большому количеству векторов. Для попарных сравнений и малых объёмов данных — Python.

---

## Деплой

- **Сервер**: `sleep-test.kuban-forum.ru` (2.26.51.8)
- **Frontend**: `/srv/sleep-test-web/frontend/dist/` (Vite build → статика)
- **Backend**: `/srv/sleep-test/backend/` (FastAPI + uvicorn)
- **Reverse proxy**: Caddy (`/etc/caddy/Caddyfile`)
- **Systemd**: `innercore-backend.service`
- **Git**: ветка `dev-sleep-test`, remote `smartor777-sketch/sleep.git`
