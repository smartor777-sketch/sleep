import os
import sys
from pathlib import Path


os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://test:test@localhost:5432/test_db")
os.environ.setdefault("JWT_SECRET_KEY", "test-secret-key")
os.environ.setdefault("JWT_ALGORITHM", "HS256")
os.environ.setdefault("JWT_ACCESS_TOKEN_EXPIRE_MINUTES", "30")
os.environ.setdefault("JWT_REFRESH_TOKEN_EXPIRE_DAYS", "7")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")
os.environ.setdefault("LLM_SERVICE_URL", "http://localhost:8001")
os.environ.setdefault("EMBEDDINGS_API_KEY", "test-embeddings-key")
os.environ.setdefault("EMBEDDINGS_BASE_URL", "https://api.cometapi.com")
os.environ.setdefault("EMBEDDINGS_MODEL", "text-embedding-3-small")

BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))
