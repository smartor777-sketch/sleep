#!/usr/bin/env bash
# Phase 4: Add Docker Hub mirror to bypass docker.io blocks (both RU IP and VLESS-exit IP banned).
# Uses Google's public mirror.gcr.io as primary; falls back to docker.io.

set -euo pipefail

if [[ $EUID -ne 0 ]]; then
  echo "Run with sudo: sudo bash $0" >&2
  exit 1
fi

echo "[mirror] === Phase 4: Docker Hub mirror ==="

# 1. Probe candidate mirrors (without VPN proxy)
echo "[mirror] probing mirror candidates (direct, no proxy)..."
declare -a CANDIDATES=(
  "https://mirror.gcr.io"
  "https://dockerhub.timeweb.cloud"
  "https://huecker.io"
)

PICKED=""
for m in "${CANDIDATES[@]}"; do
  if curl -fsS --noproxy '*' --max-time 8 "$m/v2/" >/dev/null 2>&1 \
     || curl -fsS --noproxy '*' --max-time 8 "$m/v2/library/nginx/manifests/alpine" -o /dev/null 2>&1; then
    echo "  ✅ $m  -> reachable"
    [[ -z "$PICKED" ]] && PICKED="$m"
  else
    echo "  ❌ $m  -> unreachable"
  fi
done

if [[ -z "$PICKED" ]]; then
  echo "[mirror] none of the candidates reachable directly" >&2
  echo "[mirror] will try mirror.gcr.io via VPN proxy as fallback" >&2
  PICKED="https://mirror.gcr.io"
fi

echo "[mirror] using: $PICKED"

# 2. Write /etc/docker/daemon.json
DAEMON_JSON=/etc/docker/daemon.json
if [[ -f "$DAEMON_JSON" ]]; then
  cp -a "$DAEMON_JSON" "${DAEMON_JSON}.bak.$(date +%s)"
fi

cat > "$DAEMON_JSON" <<EOF
{
  "registry-mirrors": ["$PICKED"]
}
EOF
echo "[mirror] wrote $DAEMON_JSON"

# 3. Restart docker
systemctl restart docker
sleep 3

if ! systemctl is-active --quiet docker; then
  echo "[mirror] docker FAILED to restart" >&2
  journalctl -u docker -n 20 --no-pager >&2
  exit 1
fi

docker info 2>&1 | grep -i mirror || true

# 4. Test pull through mirror
echo "[mirror] testing pull via mirror..."
if docker pull --quiet nginx:1.27-alpine; then
  echo "[mirror] ✅ pull works"
  docker rmi nginx:1.27-alpine >/dev/null 2>&1 || true
else
  echo "[mirror] ❌ pull failed — mirror may not have this image, will try alternate" >&2
  exit 1
fi

echo ""
echo "=== Phase 4 done ==="
echo "Docker now uses $PICKED as Hub mirror."
echo "VPN proxy stays enabled for non-DockerHub outbound (Google APIs etc.)."
