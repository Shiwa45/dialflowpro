#!/bin/sh
# Write configs and launch livekit-server + livekit-sip in WSL.
set -e
cd /opt/dialflow/livekit

cat > livekit.yaml << 'EOF'
port: 7880
bind_addresses:
  - 0.0.0.0
rtc:
  tcp_port: 7881
  port_range_start: 50100
  port_range_end: 50200
  use_external_ip: false
redis:
  address: 127.0.0.1:6379
keys:
  dialflowkey: c4VSDWKaKJ8sE0ZfiyJ9E3RuweBqaLByzm41mDi7mrM
logging:
  level: info
EOF

cat > sip.yaml << 'EOF'
api_key: dialflowkey
api_secret: c4VSDWKaKJ8sE0ZfiyJ9E3RuweBqaLByzm41mDi7mrM
ws_url: ws://127.0.0.1:7880
redis:
  address: 127.0.0.1:6379
sip_port: 5062
rtp_port: 10100-10200
use_external_ip: false
logging:
  level: info
EOF

# stop old instances if any
pkill -f "livekit-server --config" 2>/dev/null || true
pkill -f "livekit-sip" 2>/dev/null || true
sleep 1

nohup ./livekit-server --config livekit.yaml > server.log 2>&1 &
sleep 4
LD_LIBRARY_PATH=/opt/dialflow/livekit/lib nohup ./livekit-sip --config sip.yaml > sip.log 2>&1 &
sleep 4

echo "--- processes ---"
pgrep -af "livekit" | head -4
echo "--- server health ---"
curl -s -o /dev/null -w "http://localhost:7880 -> %{http_code}\n" http://localhost:7880
echo "--- server log tail ---"
tail -5 server.log
echo "--- sip log tail ---"
tail -8 sip.log
