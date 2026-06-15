#!/bin/sh
# Bring up the full WSL service stack: Redis, FreeSWITCH, LiveKit server+sip.
# Idempotent — safe to re-run; starts only what is down.
LKDIR=/opt/dialflow/livekit

echo "--- redis ---"
if ! redis-cli ping >/dev/null 2>&1; then
  redis-server --daemonize yes
  sleep 1
fi
redis-cli ping >/dev/null 2>&1 && echo "redis: UP" || echo "redis: FAILED"

echo "--- freeswitch ---"
if ! pgrep -x freeswitch >/dev/null 2>&1; then
  freeswitch -nc -nonat >/dev/null 2>&1 &
  sleep 8
fi
pgrep -x freeswitch >/dev/null 2>&1 && echo "freeswitch: UP" || echo "freeswitch: FAILED"

echo "--- livekit-server ---"
if ! pgrep -f "livekit-server --config" >/dev/null 2>&1; then
  cd "$LKDIR" && nohup ./livekit-server --config livekit.yaml > server.log 2>&1 &
  sleep 4
fi
pgrep -f "livekit-server --config" >/dev/null 2>&1 && echo "livekit-server: UP" || echo "livekit-server: FAILED"

echo "--- livekit-sip ---"
if ! pgrep -f "livekit-sip --config" >/dev/null 2>&1; then
  cd "$LKDIR" && LD_LIBRARY_PATH="$LKDIR/lib" nohup ./livekit-sip --config sip.yaml > sip.log 2>&1 &
  sleep 4
fi
pgrep -f "livekit-sip --config" >/dev/null 2>&1 && echo "livekit-sip: UP" || echo "livekit-sip: FAILED"

echo "--- listening ports ---"
ss -tlnp 2>/dev/null | grep -E ':6379|:8021|:7880|:7881|:5062' | awk '{print $4}' | sort -u
echo "--- wsl ip ---"
hostname -I | awk '{print $1}'
