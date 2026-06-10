#!/usr/bin/env bash
# Phase 2: tun2socks + policy routing -> all outbound through VLESS, SSH preserved.
# AUTO-REVERT: if not cancelled within 5 minutes, routing reverts to original.

set -euo pipefail

TUN2SOCKS_VERSION="${TUN2SOCKS_VERSION:-2.6.0}"
TUN2SOCKS_BIN=/usr/local/bin/tun2socks
TUN_DEV=utunvpn
TUN_IP=10.255.0.2
TUN_GW=10.255.0.1
TUN_NET=10.255.0.0/24
VPN_TABLE_ID=200
VPN_TABLE_NAME=vpn
FWMARK=0x100
SOCKS_URL="socks5://127.0.0.1:10808"

if [[ $EUID -ne 0 ]]; then
  echo "Run with sudo: sudo bash $0" >&2
  exit 1
fi

echo "[tun2socks] === Phase 2: TUN routing ==="

# Discover current default route (we MUST preserve this for SSH + xray->VLESS)
DEFAULT_LINE=$(ip route show default | head -1)
IFACE=$(awk '{for(i=1;i<=NF;i++) if($i=="dev"){print $(i+1);exit}}' <<<"$DEFAULT_LINE")
GW=$(awk '{for(i=1;i<=NF;i++) if($i=="via"){print $(i+1);exit}}' <<<"$DEFAULT_LINE")
VLESS_IP=213.176.113.167

if [[ -z "$IFACE" || -z "$GW" ]]; then
  echo "[tun2socks] Cannot determine default route iface/gw" >&2
  ip route show default >&2
  exit 1
fi

echo "[tun2socks] eth iface: $IFACE  gateway: $GW  VLESS host: $VLESS_IP"

# --- Backup routing state ---
BACKUP=/var/lib/innercore-routing-backup.txt
{
  echo "# Generated $(date -u +%FT%TZ) by 02-enable-tun.sh"
  echo "# DEFAULT_GW=$GW IFACE=$IFACE"
  ip route show
  echo "--- ip rule ---"
  ip rule show
  echo "--- iptables mangle ---"
  iptables -t mangle -S
} > "$BACKUP"
echo "[tun2socks] routing backup -> $BACKUP"

# --- Install tun2socks ---
if [[ -x "$TUN2SOCKS_BIN" ]] && "$TUN2SOCKS_BIN" -version 2>&1 | grep -q "$TUN2SOCKS_VERSION"; then
  echo "[tun2socks] already installed ($TUN2SOCKS_VERSION)"
else
  echo "[tun2socks] downloading v$TUN2SOCKS_VERSION..."
  apt-get install -y -qq unzip >/dev/null
  tmp=$(mktemp -d)
  curl -fsSL -o "$tmp/t.zip" \
    "https://github.com/xjasonlyu/tun2socks/releases/download/v${TUN2SOCKS_VERSION}/tun2socks-linux-amd64.zip"
  unzip -q "$tmp/t.zip" -d "$tmp"
  # zip contains a binary like tun2socks-linux-amd64
  bin=$(find "$tmp" -maxdepth 1 -type f -name "tun2socks*" ! -name "*.zip" | head -1)
  install -m 755 "$bin" "$TUN2SOCKS_BIN"
  rm -rf "$tmp"
fi
"$TUN2SOCKS_BIN" -version 2>&1 | head -1 || true

# --- Ensure rt_tables has our entry ---
if ! grep -q "^$VPN_TABLE_ID $VPN_TABLE_NAME" /etc/iproute2/rt_tables; then
  echo "$VPN_TABLE_ID $VPN_TABLE_NAME" >> /etc/iproute2/rt_tables
fi

# --- systemd unit for tun2socks ---
cat > /etc/systemd/system/tun2socks.service <<EOF
[Unit]
Description=tun2socks - userspace TUN bridge to SOCKS5
Documentation=https://github.com/xjasonlyu/tun2socks
After=xray.service
Requires=xray.service

[Service]
Type=simple
ExecStartPre=-/sbin/ip link del $TUN_DEV
ExecStartPre=/sbin/ip tuntap add mode tun dev $TUN_DEV
ExecStartPre=/sbin/ip addr add $TUN_IP/24 dev $TUN_DEV
ExecStartPre=/sbin/ip link set dev $TUN_DEV up
ExecStart=$TUN2SOCKS_BIN -device $TUN_DEV -proxy $SOCKS_URL -loglevel warn
ExecStopPost=-/sbin/ip link del $TUN_DEV
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable tun2socks
systemctl restart tun2socks
sleep 3

if ! systemctl is-active --quiet tun2socks; then
  echo "[tun2socks] service FAILED" >&2
  journalctl -u tun2socks -n 30 --no-pager >&2
  exit 1
fi

ip link show "$TUN_DEV" >/dev/null || { echo "[tun2socks] $TUN_DEV not created" >&2; exit 1; }
echo "[tun2socks] $TUN_DEV is up"

# --- Build revert script (will be called by auto-revert OR by user) ---
REVERT=/usr/local/sbin/innercore-revert-routing.sh
cat > "$REVERT" <<EOF
#!/usr/bin/env bash
# Auto-revert routing to direct-via-$IFACE state.
set +e
ip route del $VLESS_IP via $GW dev $IFACE
ip rule del fwmark $FWMARK priority 100 lookup main
ip rule del priority 110 lookup $VPN_TABLE_NAME
ip route flush table $VPN_TABLE_NAME
iptables -t mangle -D PREROUTING -i $IFACE -j CONNMARK --restore-mark
iptables -t mangle -D PREROUTING -i $IFACE -j MARK --set-mark $FWMARK
iptables -t mangle -D PREROUTING -i $IFACE -j CONNMARK --save-mark
iptables -t mangle -D OUTPUT -j CONNMARK --restore-mark
systemctl stop tun2socks
echo "[\$(date -u +%FT%TZ)] routing reverted" >> /var/log/innercore-vpn-revert.log
EOF
chmod +x "$REVERT"

# --- Apply routing ---
echo "[tun2socks] applying policy routing..."

# 1. Pin VLESS server to direct route (CRITICAL — prevents loop)
ip route replace "$VLESS_IP" via "$GW" dev "$IFACE"

# 2. Build VPN table: default via utun
ip route flush table "$VPN_TABLE_NAME" 2>/dev/null || true
ip route add default dev "$TUN_DEV" table "$VPN_TABLE_NAME"

# 3. fwmark-based rules
ip rule del fwmark $FWMARK priority 100 2>/dev/null || true
ip rule del priority 110 lookup $VPN_TABLE_NAME 2>/dev/null || true
ip rule add fwmark $FWMARK priority 100 lookup main
ip rule add priority 110 lookup $VPN_TABLE_NAME

# 4. iptables: mark traffic ARRIVING on eth0, preserve for replies
iptables -t mangle -C PREROUTING -i "$IFACE" -j CONNMARK --restore-mark 2>/dev/null \
  || iptables -t mangle -A PREROUTING -i "$IFACE" -j CONNMARK --restore-mark
iptables -t mangle -C PREROUTING -i "$IFACE" -j MARK --set-mark $FWMARK 2>/dev/null \
  || iptables -t mangle -A PREROUTING -i "$IFACE" -j MARK --set-mark $FWMARK
iptables -t mangle -C PREROUTING -i "$IFACE" -j CONNMARK --save-mark 2>/dev/null \
  || iptables -t mangle -A PREROUTING -i "$IFACE" -j CONNMARK --save-mark
iptables -t mangle -C OUTPUT -j CONNMARK --restore-mark 2>/dev/null \
  || iptables -t mangle -A OUTPUT -j CONNMARK --restore-mark

# --- Schedule auto-revert ---
nohup bash -c "sleep 300 && $REVERT" </dev/null >>/var/log/innercore-vpn-revert.log 2>&1 &
echo $! > /var/run/innercore-vpn-revert.pid
disown

# --- Self-test ---
sleep 2
echo ""
echo "=== Phase 2 applied. Self-test ==="
echo "VPN exit IP (via utun): $(curl -fsS --max-time 10 https://ifconfig.me || echo FAIL)"
echo ""
echo "AUTO-REVERT scheduled in 5 minutes (PID $(cat /var/run/innercore-vpn-revert.pid))"
echo ""
echo "If SSH stays alive AND curl shows VLESS exit IP:"
echo "  sudo kill \$(cat /var/run/innercore-vpn-revert.pid)"
echo "  echo 'OK, routing persisted'"
echo ""
echo "If anything is wrong — just wait 5 min, it auto-reverts."
echo "Or force-revert now:  sudo $REVERT"
