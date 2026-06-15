#!/bin/sh
# Download livekit-server + livekit-sip latest linux amd64 binaries.
set -e
mkdir -p /opt/dialflow/livekit
cd /opt/dialflow/livekit

echo "--- resolving latest releases ---"
SRV_URL=$(curl -s https://api.github.com/repos/livekit/livekit/releases/latest \
  | grep browser_download_url | grep linux_amd64.tar.gz | head -1 | cut -d'"' -f4)
SIP_URL=$(curl -s https://api.github.com/repos/livekit/sip/releases/latest \
  | grep browser_download_url | grep linux_amd64.tar.gz | head -1 | cut -d'"' -f4)
echo "server: $SRV_URL"
echo "sip:    $SIP_URL"

echo "--- downloading ---"
curl -sL "$SRV_URL" -o lk-server.tar.gz
curl -sL "$SIP_URL" -o lk-sip.tar.gz
tar xzf lk-server.tar.gz
tar xzf lk-sip.tar.gz
rm -f lk-server.tar.gz lk-sip.tar.gz
chmod +x livekit-server livekit-sip 2>/dev/null || true
ls -la
echo "--- versions ---"
./livekit-server --version || true
./livekit-sip --version 2>/dev/null || echo "(sip has no --version; binary present)"
