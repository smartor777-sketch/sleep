"""Подключение к базе данных"""

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from sqlalchemy import text
from config import settings

# Создаем async engine
engine = create_async_engine(
    str(settings.database_url),
    echo=settings.log_level == "DEBUG",
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20
)

# Создаем sessionmaker
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False
)

# Base для моделей
Base = declarative_base()


async def get_db() -> AsyncSession:
    """
    Dependency для получения сессии БД
    
    Yields:
        AsyncSession: Сессия базы данных
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


async def init_db():
    """
    Инициализация базы данных (создание таблиц)
    """
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        await _apply_schema_upgrades(conn)


async def close_db():
    """
    Закрытие соединения с базой данных
    """
    await engine.dispose()


async def _apply_schema_upgrades(conn):
    """Lightweight schema upgrades for environments without Alembic."""
    statements = [
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS onboarding_completed BOOLEAN NOT NULL DEFAULT FALSE",
        "ALTER TABLE dreams ADD COLUMN IF NOT EXISTS gradient_color_1 VARCHAR(7)",
        "ALTER TABLE dreams ADD COLUMN IF NOT EXISTS gradient_color_2 VARCHAR(7)",
        "ALTER TABLE dreams ADD COLUMN IF NOT EXISTS embedding_text TEXT",
        "ALTER TABLE dreams ADD COLUMN IF NOT EXISTS embedding_model VARCHAR(128)",
        "ALTER TABLE dreams ADD COLUMN IF NOT EXISTS embedding_updated_at TIMESTAMPTZ",
        "ALTER TABLE dreams ALTER COLUMN title TYPE VARCHAR(64)",
        """
        CREATE TABLE IF NOT EXISTS user_archetypes (
            id UUID PRIMARY KEY,
            user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            name VARCHAR(128) NOT NULL,
            count INTEGER NOT NULL DEFAULT 0,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )
        """,
        "CREATE UNIQUE INDEX IF NOT EXISTS uq_user_archetype_name ON user_archetypes(user_id, name)",
        """
        CREATE TABLE IF NOT EXISTS dream_chunks (
            id UUID PRIMARY KEY,
            dream_id UUID NOT NULL REFERENCES dreams(id) ON DELETE CASCADE,
            user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            chunk_index INTEGER NOT NULL,
            text TEXT NOT NULL,
            embedding_text TEXT,
            embedding_model VARCHAR(128),
            metadata_json JSONB,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )
        """,
        "CREATE INDEX IF NOT EXISTS ix_dream_chunks_dream_id ON dream_chunks(dream_id)",
        "CREATE INDEX IF NOT EXISTS ix_dream_chunks_user_id ON dream_chunks(user_id)",
        """
        CREATE TABLE IF NOT EXISTS dream_symbols (
            id UUID PRIMARY KEY,
            user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            dream_id UUID NOT NULL REFERENCES dreams(id) ON DELETE CASCADE,
            chunk_id UUID REFERENCES dream_chunks(id) ON DELETE CASCADE,
            symbol_name VARCHAR(128) NOT NULL,
            weight INTEGER,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )
        """,
        "CREATE INDEX IF NOT EXISTS ix_dream_symbols_user_id ON dream_symbols(user_id)",
        "CREATE INDEX IF NOT EXISTS ix_dream_symbols_dream_id ON dream_symbols(dream_id)",
        "CREATE INDEX IF NOT EXISTS ix_dream_symbols_symbol_name ON dream_symbols(symbol_name)",
        """
        CREATE TABLE IF NOT EXISTS dream_symbol_entities (
            id UUID PRIMARY KEY,
            user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            dream_id UUID NOT NULL REFERENCES dreams(id) ON DELETE CASCADE,
            chunk_id UUID REFERENCES dream_chunks(id) ON DELETE CASCADE,
            canonical_name VARCHAR(128) NOT NULL,
            display_label VARCHAR(128) NOT NULL,
            entity_type VARCHAR(32) NOT NULL DEFAULT 'symbol',
            weight DOUBLE PRECISION NOT NULL DEFAULT 1.0,
            related_archetypes_json JSONB,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )
        """,
        "CREATE INDEX IF NOT EXISTS ix_dream_symbol_entities_user_id ON dream_symbol_entities(user_id)",
        "CREATE INDEX IF NOT EXISTS ix_dream_symbol_entities_dream_id ON dream_symbol_entities(dream_id)",
        "CREATE INDEX IF NOT EXISTS ix_dream_symbol_entities_chunk_id ON dream_symbol_entities(chunk_id)",
        "CREATE INDEX IF NOT EXISTS ix_dream_symbol_entities_canonical_name ON dream_symbol_entities(canonical_name)",
        """
        CREATE TABLE IF NOT EXISTS dream_archetypes (
            id UUID PRIMARY KEY,
            user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            dream_id UUID NOT NULL REFERENCES dreams(id) ON DELETE CASCADE,
            archetype_name VARCHAR(128) NOT NULL,
            delta INTEGER NOT NULL DEFAULT 1,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )
        """,
        "CREATE INDEX IF NOT EXISTS ix_dream_archetypes_user_id ON dream_archetypes(user_id)",
        "CREATE INDEX IF NOT EXISTS ix_dream_archetypes_dream_id ON dream_archetypes(dream_id)",
    ]
    for sql in statements:
        await conn.execute(text(sql))
