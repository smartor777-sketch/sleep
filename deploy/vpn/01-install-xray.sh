#!/usr/bin/env bash
# Phase 1: Install Xray-core + configure VLESS outbound + SOCKS5 inbound.
# Idempotent. Does NOT touch routing — SOCKS5 only on 127.0.0.1.
# After this script: test with `curl --socks5 127.0.0.1:10808 https://ifconfig.me`.

set -euo pipefail

XRAY_VERSION="${XRAY_VERSION:-26.3.27}"   # https://github.com/XTLS/Xray-core/releases
XRAY_BIN=/usr/local/bin/xray
XRAY_DIR=/usr/local/etc/xray
XRAY_LOG=/var/log/xray
SOCKS_PORT=10808

if [[ $EUID -ne 0 ]]; then
  echo "Run with sudo: sudo bash $0" >&2
  exit 1
fi

echo "[xray] === Phase 1: install + configure ==="
echo "[xray] target version: $XRAY_VERSION"

# Install deps
apt-get update -qq
apt-get install -y -qq unzip curl ca-certificates

# Download Xray if not present
if [[ -x "$XRAY_BIN" ]] && "$XRAY_BIN" version 2>/dev/null | grep -q "$XRAY_VERSION"; then
  echo "[xray] already installed at $XRAY_BIN ($XRAY_VERSION)"
else
  echo "[xray] downloading Xray-core $XRAY_VERSION..."
  tmp=$(mktemp -d)
  curl -fsSL -o "$tmp/xray.zip" \
    "https://github.com/XTLS/Xray-core/releases/download/v${XRAY_VERSION}/Xray-linux-64.zip"
  unzip -q "$tmp/xray.zip" -d "$tmp"
  install -m 755 "$tmp/xray" "$XRAY_BIN"
  rm -rf "$tmp"
fi

"$XRAY_BIN" version | head -1

# Create dirs
install -d -m 755 "$XRAY_DIR"
install -d -m 755 "$XRAY_LOG"

# Write config
cat > "$XRAY_DIR/config.json" <<'EOF'
{
  "log": {
    "loglevel": "warning",
    "access": "/var/log/xray/access.log",
    "error": "/var/log/xray/error.log"
  },
  "inbounds": [
    {
      "tag": "socks-in",
      "listen": "127.0.0.1",
      "port": 10808,
      "protocol": "socks",
      "settings": {
        "udp": true,
        "auth": "noauth"
      },
      "sniffing": {
        "enabled": true,
        "destOverride": ["http", "tls", "quic"]
      }
    },
    {
      "tag": "http-in",
      "listen": "127.0.0.1",
      "port": 10809,
      "protocol": "http",
      "settings": {}
    }
  ],
  "outbounds": [
    {
      "tag": "vless-out",
      "protocol": "vless",
      "settings": {
        "vnext": [
          {
            "address": "213.176.113.167",
            "port": 8443,
            "users": [
              {
                "id": "e4912841-c54f-432c-9ca6-6bf5f042a079",
                "flow": "",
                "encryption": "none"
              }
            ]
          }
        ]
      },
      "streamSettings": {
        "network": "tcp",
        "security": "reality",
        "realitySettings": {
          "fingerprint": "chrome",
          "serverName": "www.vu.nl",
          "publicKey": "RxwH9sa2I90bolNibAwwBNvp9ZYOPE9l3U9b3Ghu60o",
          "shortId": "82",
          "spiderX": "/"
        }
      }
    },
    {
      "tag": "direct",
      "protocol": "freedom",
      "settings": {}
    },
    {
      "tag": "block",
      "protocol": "blackhole",
      "settings": {}
    }
  ],
  "routing": {
    "domainStrategy": "AsIs",
    "rules": [
      {
        "type": "field",
        "ip": [
          "10.0.0.0/8",
          "172.16.0.0/12",
          "192.168.0.0/16",
          "127.0.0.0/8",
          "169.254.0.0/16",
          "::1/128",
          "fc00::/7",
          "fe80::/10"
        ],
        "outboundTag": "direct"
      }
    ]
  }
}
EOF

# systemd unit
cat > /etc/systemd/system/xray.service <<EOF
[Unit]
Description=Xray-core VLESS client
Documentation=https://github.com/XTLS/Xray-core
After=network-online.target nss-lookup.target
Wants=network-online.target

[Service]
Type=simple
User=root
ExecStart=${XRAY_BIN} run -config ${XRAY_DIR}/config.json
Restart=on-failure
RestartSec=5
LimitNOFILE=65536
NoNewPrivileges=true

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable xray
systemctl restart xray
sleep 2

if systemctl is-active --quiet xray; then
  echo "[xray] service is running"
else
  echo "[xray] service FAILED, last logs:" >&2
  journalctl -u xray -n 30 --no-pager >&2
  exit 1
fi

ss -tlnp | grep -E ":(10808|10809) " || { echo "[xray] SOCKS port not listening" >&2; exit 1; }

echo ""
echo "=== Phase 1 done. Self-test ==="
echo "Direct IP   :  $(curl -fsS --max-time 5 https://ifconfig.me || echo FAIL)"
echo "Through VPN :  $(curl -fsS --max-time 10 --socks5 127.0.0.1:${SOCKS_PORT} https://ifconfig.me || echo FAIL)"
echo ""
echo "If 'Through VPN' shows a non-Russian IP — Phase 1 OK."
echo "Next: phase 2 (TUN routing). Don't run it yet."
