#!/bin/bash
# systemd-deploy.sh — deploy InnerCore on prod (sleep.kuban-forum.ru, 87.120.186.100).
#
# Actual prod is bare-metal systemd (NO docker):
#   - backend   : innercore-prod.service  (uvicorn :8000, venv /srv/sleep-prod/backend/backend/.venv)
#   - llm       : innercore-llm.service   (uvicorn :8001, venv /srv/sleep-prod/backend/llm_service/.venv)
#   - celery    : celery-prod.service     (+ drop-in --autoscale=2,1 --max-memory-per-child=300000)
#   - frontend  : static built from frontend/dist, served by Caddy (sleep.kuban-forum.ru)
#   - postgres  : native PostgreSQL 17 (systemd), redis native (systemd)
#
# Run on the server as root:
#   bash /srv/sleep-prod/backend/deploy/systemd-deploy.sh [git_ref]
#     git_ref — branch/tag/commit to deploy (default: origin/dev-sleep-test)
#
# Steps: git checkout → venv+pip (backend, llm) → npm build (frontend) → restart services.

set -euo pipefail

APP_DIR="${APP_DIR:-/srv/sleep-prod/backend}"
GIT_REF="${1:-origin/dev-sleep-test}"
SERVICES=(innercore-llm innercore-prod celery-prod)

cd "$APP_DIR"
echo "[deploy] $(date -u +%FT%TZ) ref=$GIT_REF dir=$APP_DIR"

# 1. Get the code
git fetch --all --tags
git checkout --force "$GIT_REF"
git log --oneline -1

# 2. Backend venv + pip
echo '[deploy] backend venv + pip...'
python3 -m venv "$APP_DIR/backend/.venv"
"$APP_DIR/backend/.venv/bin/pip" install --quiet --upgrade pip
"$APP_DIR/backend/.venv/bin/pip" install --quiet -r "$APP_DIR/backend/requirements.txt"

# 3. LLM service venv + pip
echo '[deploy] llm_service venv + pip...'
python3 -m venv "$APP_DIR/llm_service/.venv"
"$APP_DIR/llm_service/.venv/bin/pip" install --quiet -r "$APP_DIR/llm_service/requirements.txt"

# 4. Frontend build
echo '[deploy] frontend build...'
cd "$APP_DIR/frontend"
npm ci 2>&1 | tail -3
npm run build 2>&1 | tail -8
cd "$APP_DIR"

# 5. Restart services
#
# IMPORTANT: pip install may have rebuilt/replaced C-extension .so files
# (SQLAlchemy Cython, pydantic_core, etc.) on disk. A running process keeps
# the OLD native library pages mapped in memory; the next call into the new
# .so aborts with SIGILL/SIGSEGV (real incident 2026-08-18: celery worker
# crashed with "invalid opcode" in immutabledict.so, dreams stuck in pending).
# A full restart is therefore MANDATORY after every pip install.
systemctl daemon-reload
for svc in "${SERVICES[@]}"; do
  echo "[deploy] restart $svc"
  systemctl restart "$svc"
done

# 6. Health check
sleep 8
for svc in "${SERVICES[@]}"; do
  printf '%-20s %s\n' "$svc" "$(systemctl is-active "$svc" 2>&1)"
done
echo '=== LISTEN ==='
ss -tlnp | grep -E ':(8000|8001)\b' || true

# 7. Errors?
for svc in "${SERVICES[@]}"; do
  if [ "$(systemctl is-active "$svc")" != "active" ]; then
    echo "--- $svc ---"
    journalctl -u "$svc" --no-pager -n 15 2>&1 | tail -15
  fi
done

echo '[deploy] DONE'