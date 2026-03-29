# InnerCore

AI-powered mobile dream journal with Jungian-style analysis, contextual dream chat, and a symbolic Dream Map.

## v0.3 Highlights

- Automatic analysis after save. A dream appears in the list immediately and analysis runs in the background.
- New 3-column dream grid for faster scanning.
- Improved dream cards (title/date presentation and analysis states).
- Updated onboarding flow with a guided multi-step modal.
- Voice dream capture (MVP): local recording + transcription.
- New Dream Map with symbolic nodes, archetype filters, detail view, and manual refresh.
- Bottom navigation with icon-based sections.
- Better analysis stability, clearer loading behavior, and improved mobile responsiveness.
- Markdown rendering in analysis and chat responses.
- Bounded map area (no cyclic infinite scrolling).
- Map filters now show the full available archetype set.

## Architecture

```text
Flutter Client (iOS/Android)
        |
        v
FastAPI Backend  <-->  PostgreSQL
        |                Redis
        |                MinIO
        v
Celery Worker
        |
        +--> LLM Service (FastAPI wrapper over Gonka/OpenAI-compatible chat)
        +--> CometAPI Embeddings + Transcriptions
```

## Tech Stack

- Client: Flutter, Provider, flutter_secure_storage, flutter_markdown
- Backend: FastAPI, SQLAlchemy async, PostgreSQL, Redis, Celery, MinIO, JWT
- LLM: Gonka Proxy (OpenAI-compatible)
- Embeddings/STT: CometAPI (`text-embedding-3-small`, `whisper-1`)
- Infra: Docker, Docker Compose

## Quick Start

### Prerequisites

- Docker + Docker Compose
- Flutter SDK (for mobile client)
- Valid API credentials for:
  - Gonka (`GONKA_API_KEY`)
  - CometAPI embeddings/transcriptions (`EMBEDDINGS_API_KEY`, `TRANSCRIPTIONS_API_KEY`)

### Run backend stack

```bash
docker-compose up --build
```

Services:
- Backend API: `http://localhost:8000`
- LLM Service: `http://localhost:8001`
- PostgreSQL: `localhost:5432`
- Redis: `localhost:6379`
- MinIO API: `http://localhost:9000`
- MinIO Console: `http://localhost:9001`

### Run Flutter client

```bash
cd client
flutter pub get
flutter run --dart-define=API_BASE_URL=http://localhost:8000
```

For a real phone, replace `localhost` with your backend host or domain:

```bash
flutter run --dart-define=API_BASE_URL=https://your-domain.com
```

### Health checks

```bash
curl http://localhost:8000/health
curl http://localhost:8001/health
```

## API

- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

Core endpoint groups:
- `/api/v1/auth` - anonymous auth + account auth flows
- `/api/v1/dreams` - create/read/update/delete/search dreams
- `/api/v1/analyses` - async dream analysis lifecycle
- `/api/v1/messages` - dream chat messages
- `/api/v1/map` - Dream Map nodes, filters, details
- `/api/v1/users/me` - profile data
- `/api/v1/stats/me` - personal stats

## Development

### Run without Docker

```bash
# Backend
cd backend
pip install -r requirements.txt
uvicorn main:app --reload

# LLM service
cd llm_service
pip install -r requirements.txt
uvicorn main:app --reload --port 8001

# Celery worker
cd backend
celery -A celery_app worker --loglevel=info
```

## Contact

- Telegram: [@CoreEuler](https://t.me/CoreEuler)
- GitHub: [core-euler](https://github.com/core-euler)

## License

[MIT License](LICENSE.md)
