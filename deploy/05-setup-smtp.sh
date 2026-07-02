#!/usr/bin/env bash
# Interactive SMTP setup for InnerCore backend.
# Updates ~/innercore/deploy/.env, restarts backend + celery_worker,
# then sends a test email via docker exec.

set -euo pipefail

ENV_FILE=~/innercore/deploy/.env

if [[ ! -f "$ENV_FILE" ]]; then
  echo "[smtp] $ENV_FILE not found" >&2
  exit 1
fi

cd ~/innercore/deploy

echo "=== InnerCore SMTP setup ==="
echo "Текущие значения в .env (без паролей):"
echo "  SMTP_HOST   = $(grep "^SMTP_HOST="  .env | cut -d= -f2-)"
echo "  SMTP_PORT   = $(grep "^SMTP_PORT="  .env | cut -d= -f2- | cut -d'#' -f1 | xargs)"
echo "  SMTP_USER   = $(grep "^SMTP_USER="  .env | cut -d= -f2-)"
echo "  SMTP_FROM   = $(grep "^SMTP_FROM="  .env | cut -d= -f2-)"
echo "  SMTP_USE_SSL= $(grep "^SMTP_USE_SSL=" .env | cut -d= -f2-)"
echo ""

read -rp "SMTP host (reg.ru обычно mail.hosting.reg.ru): " SMTP_HOST
read -rp "SMTP port (465=SSL, 587=STARTTLS) [465]: " SMTP_PORT
SMTP_PORT=${SMTP_PORT:-465}
read -rp "SMTP user (полный email, login): " SMTP_USER
read -rsp "SMTP password (не отображается): " SMTP_PASSWORD; echo
read -rp "SMTP from (что отправитель показывает; обычно тот же email): " SMTP_FROM

if [[ "$SMTP_PORT" == "465" ]]; then
  SMTP_USE_SSL="true"
else
  SMTP_USE_SSL="false"
fi

# Update each field in .env using awk for safety (handles delete/replace + comment strip)
python3 - <<PY
import re, os, sys
path = "$ENV_FILE"
updates = {
    "SMTP_HOST":    """$SMTP_HOST""",
    "SMTP_PORT":    """$SMTP_PORT""",
    "SMTP_USER":    """$SMTP_USER""",
    "SMTP_PASSWORD":"""$SMTP_PASSWORD""",
    "SMTP_FROM":    """$SMTP_FROM""",
    "SMTP_USE_SSL": """$SMTP_USE_SSL""",
}
lines = open(path).read().splitlines()
keys_left = set(updates)
out = []
for line in lines:
    m = re.match(r'^([A-Z_]+)=', line)
    if m and m.group(1) in updates:
        k = m.group(1)
        out.append(f"{k}={updates[k]}")
        keys_left.discard(k)
    else:
        out.append(line)
for k in keys_left:
    out.append(f"{k}={updates[k]}")
open(path, "w").write("\n".join(out) + "\n")
os.chmod(path, 0o600)
print("[smtp] .env updated for keys:", ", ".join(updates))
PY

echo ""
echo "[smtp] restarting backend + celery_worker..."
docker compose -f docker-compose.prod.yml up -d --force-recreate backend celery_worker 2>&1 | tail -5
sleep 4

echo ""
echo "[smtp] sending test email to $SMTP_USER via backend (uses prod EmailService)..."
docker exec innercore_backend python - <<'PY'
import sys
try:
    from services.email_service import EmailService
    es = EmailService()
    target = es.smtp_user  # send to self
    es._send_email(target, "InnerCore SMTP test", "Hello from InnerCore — SMTP is alive.", html=False)
    print(f"[smtp] OK — sent test email to {target}")
except Exception as e:
    print(f"[smtp] FAILED: {type(e).__name__}: {e}", file=sys.stderr)
    sys.exit(1)
PY

echo ""
echo "=== Готово ==="
echo "Проверь почтовый ящик ($SMTP_USER) — должно быть письмо 'InnerCore SMTP test'."
echo "Если письма нет — посмотри в логи: docker compose -f docker-compose.prod.yml logs backend | grep -i smtp"
