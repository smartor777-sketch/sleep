#!/usr/bin/env bash
# Phase 3: Docker daemon + system HTTP proxy via Xray SOCKS5/HTTP.
# No routing changes. Xray must be running (Phase 1 done).

set -euo pipefail

if [[ $EUID -ne 0 ]]; then
  echo "Run with sudo: sudo bash $0" >&2
  exit 1
fi

echo "[proxy] === Phase 3: Docker + system HTTP proxy ==="

# Sanity-check Xray is up
if ! systemctl is-active --quiet xray; then
  echo "[proxy] xray.service is NOT running — Phase 1 must be done first" >&2
  exit 1
fi
if ! ss -tlnp 2>/dev/null | grep -q "127.0.0.1:10809"; then
  echo "[proxy] Xray HTTP inbound on 127.0.0.1:10809 not listening" >&2
  exit 1
fi

# --- Clean up Phase 2 leftovers (TUN approach) ---
echo "[proxy] cleaning up Phase 2 artefacts..."
systemctl disable --now tun2socks.service 2>/dev/null || true
rm -f /etc/systemd/system/tun2socks.service
ip link del utunvpn 2>/dev/null || true
ip rule del fwmark 0x100 priority 100 2>/dev/null || true
ip rule del priority 110 lookup vpn 2>/dev/null || true
ip route flush table vpn 2>/dev/null || true
iptables -t mangle -D PREROUTING -i eth0 -j CONNMARK --restore-mark 2>/dev/null || true
iptables -t mangle -D PREROUTING -i eth0 -j MARK --set-mark 0x100 2>/dev/null || true
iptables -t mangle -D PREROUTING -i eth0 -j CONNMARK --save-mark 2>/dev/null || true
iptables -t mangle -D OUTPUT -j CONNMARK --restore-mark 2>/dev/null || true
sed -i '/^200 vpn$/d' /etc/iproute2/rt_tables 2>/dev/null || true
systemctl daemon-reload

# --- 1. Docker daemon proxy ---
DOCKER_OVERRIDE_DIR=/etc/systemd/system/docker.service.d
install -d -m 755 "$DOCKER_OVERRIDE_DIR"

cat > "$DOCKER_OVERRIDE_DIR/http-proxy.conf" <<EOF
[Service]
Environment="HTTP_PROXY=http://127.0.0.1:10809"
Environment="HTTPS_PROXY=http://127.0.0.1:10809"
Environment="NO_PROXY=localhost,127.0.0.0/8,::1,*.docker.internal,*.local"
EOF
echo "[proxy] wrote $DOCKER_OVERRIDE_DIR/http-proxy.conf"

systemctl daemon-reload
systemctl restart docker
sleep 3

if ! systemctl is-active --quiet docker; then
  echo "[proxy] docker FAILED to restart" >&2
  journalctl -u docker -n 30 --no-pager >&2
  exit 1
fi

# --- 2. Test docker pull through proxy ---
echo "[proxy] testing docker pull through proxy..."
if docker pull --quiet nginx:1.27-alpine; then
  echo "[proxy] ✅ docker pull works through VPN"
else
  echo "[proxy] ❌ docker pull failed" >&2
  exit 1
fi

# --- 3. System-wide HTTP proxy for shell tools (curl/wget/apt) ---
# Place in /etc/profile.d so it loads for all interactive shells
cat > /etc/profile.d/innercore-proxy.sh <<'EOF'
# InnerCore VPN proxy for shell tools (curl/wget/apt/etc.)
# Comment out if you want direct access from shell.
export http_proxy=http://127.0.0.1:10809
export https_proxy=http://127.0.0.1:10809
export HTTP_PROXY=http://127.0.0.1:10809
export HTTPS_PROXY=http://127.0.0.1:10809
export no_proxy="localhost,127.0.0.0/8,::1,*.docker.internal,*.local,5.42.100.202"
export NO_PROXY="$no_proxy"
EOF
chmod 644 /etc/profile.d/innercore-proxy.sh
echo "[proxy] wrote /etc/profile.d/innercore-proxy.sh"

# --- 4. APT proxy (works regardless of shell) ---
cat > /etc/apt/apt.conf.d/95innercore-proxy <<EOF
Acquire::http::Proxy "http://127.0.0.1:10809";
Acquire::https::Proxy "http://127.0.0.1:10809";
EOF
echo "[proxy] wrote /etc/apt/apt.conf.d/95innercore-proxy"

echo ""
echo "=== Phase 3 done ==="
echo "Re-login shell or 'source /etc/profile.d/innercore-proxy.sh' to pick up env."
echo ""
echo "Self-tests:"
echo "  Direct  (no proxy):  curl -fsS --noproxy '*' https://ifconfig.me"
echo "  Through proxy:       curl -fsS https://ifconfig.me"
echo "  Docker pull works:   docker pull hello-world"
