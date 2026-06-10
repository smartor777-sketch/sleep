#!/usr/bin/env bash
# Server-side deploy script. Runs on msk-1 after CI builds & pushes images.
# Triggered via SSH from GitHub Actions.
#
# Required env (passed by CI):
#   IMAGE_TAG   - git SHA tag of images to deploy (e.g. "main-abc1234")
#   GHCR_USER   - GitHub username for ghcr.io login
#   GHCR_TOKEN  - GitHub PAT or GITHUB_TOKEN

set -euo pipefail

cd "$(dirname "$0")"

if [[ -z "${IMAGE_TAG:-}" ]]; then
  echo "[deploy] IMAGE_TAG is required" >&2
  exit 1
fi

echo "[deploy] $(date -u +%FT%TZ) IMAGE_TAG=$IMAGE_TAG"

# Login to GHCR (only if creds provided — local re-runs can skip)
if [[ -n "${GHCR_USER:-}" && -n "${GHCR_TOKEN:-}" ]]; then
  echo "$GHCR_TOKEN" | docker login ghcr.io -u "$GHCR_USER" --password-stdin
fi

# .env must exist beside this script
if [[ ! -f .env ]]; then
  echo "[deploy] .env not found in $(pwd) — bootstrap it first" >&2
  exit 1
fi

export IMAGE_TAG

echo "[deploy] pulling images..."
docker compose -f docker-compose.prod.yml pull

echo "[deploy] starting services..."
docker compose -f docker-compose.prod.yml up -d --remove-orphans

echo "[deploy] pruning old images..."
docker image prune -f --filter "until=24h" || true

echo "[deploy] health check..."
sleep 5
docker compose -f docker-compose.prod.yml ps

echo "[deploy] done"
