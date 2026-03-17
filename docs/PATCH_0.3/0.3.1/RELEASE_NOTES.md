# JungAI v0.3.1 — Release Notes

Date: 2026-03-17

## Bug Fixes

### Chat retries (Issue 1)
- `reply_to_dream_chat_task` now has retry configuration matching `analyze_dream_task`: `autoretry_for=(LLMTransientError,)`, exponential backoff (max 120s), jitter, up to 4 retries.
- Separated exception handling: `LLMTransientError` logged as warning (transient), other exceptions logged as error.
- **Before:** a single LLM timeout killed the chat task permanently; user never got a reply.
- **After:** task retries up to 4 times with backoff before giving up.

### Analysis stuck in PENDING (Issue 2)
- Fixed the `LLMTransientError` handler in `_analyze_dream_async`: when `self.request.retries >= self.max_retries`, analysis status is now set to `FAILED` with `"Max retries exhausted: ..."` error message.
- **Before:** after exhausting all Celery retries, analysis remained in `PENDING` forever — client showed an infinite spinner.
- **After:** analysis correctly transitions to `FAILED`, client can show an error and offer a retry button.

## New Features

### CometAPI fallback provider (Issue 3)
- Added `CometApiProvider` (`llm_service/providers/comet_api.py`) — OpenAI-compatible fallback provider with no internal retries.
- Reuses `_normalize_message` and `_extract_content` from `GonkaProxyProvider` for consistency.
- LLM Service config (`llm_service/config.py`) extended with optional `comet_api_key`, `comet_base_url`, `comet_model` settings.
- `/analyze` and `/chat` endpoints in `llm_service/main.py` now attempt the primary Gonka Proxy provider first; on any failure, automatically fall back to CometAPI (if configured).
- `docker-compose.yml` updated with `COMET_API_KEY`, `COMET_BASE_URL`, `COMET_MODEL` environment variables for `llm_service`.
- **Effect:** when Gonka Proxy is down, requests are transparently served by CometAPI (gpt-5.1) instead of failing.

### Archetypes pie chart (UI)
- Profile screen: replaced linear progress bars with a `PieChart` (fl_chart) for archetype distribution.
- Each archetype gets a distinct color from a 10-color palette; percentage labels shown on sectors.
- Legend with colored dots and counts displayed below the chart.

## Files Changed

| Action   | File                                    |
|----------|-----------------------------------------|
| Modified | `backend/tasks.py`                      |
| Created  | `llm_service/providers/comet_api.py`    |
| Modified | `llm_service/config.py`                 |
| Modified | `llm_service/main.py`                   |
| Modified | `docker-compose.yml`                    |
| Modified | `client/lib/screens/profile_screen.dart` |
