#!/bin/sh
set -e
mkdir -p /opt/dialflow/livekit
cd /opt/dialflow/livekit

echo "--- 1. livekit-server binary ---"
if [ ! -x livekit-server ]; then
  curl -sL https://github.com/livekit/livekit/releases/download/v1.13.1/livekit_1.13.1_linux_amd64.tar.gz -o s.tgz
  tar xzf s.tgz && rm -f s.tgz
fi
./livekit-server --version

echo "--- 2. opus runtime present? (needed by livekit-sip) ---"
ldconfig -p | grep -E "libopus|libsoxr" || echo "NO_OPUS_LIBS"

echo "--- 3. python3 available for registry pull? ---"
command -v python3 && python3 --version || echo "NO_PYTHON3"
