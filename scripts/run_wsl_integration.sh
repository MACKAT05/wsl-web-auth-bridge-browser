#!/usr/bin/env bash
set -euo pipefail
REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
export PATH="$HOME/.local/bin:$PATH"
export WEB_AUTH_CALLBACK_PORT=45678
export SF_AUTH_SOCKET_PORT=45678

echo "=== WSL integration test (dbt/schemachange style) ==="
echo "WSL IP: $(hostname -I | awk '{print $1}')"
echo "Windows gateway: $(awk '/nameserver/{print $2; exit}' /etc/resolv.conf)"

echo ""
echo "--- Step 1: doctor ---"
if wsl-web-auth-bridge-client doctor; then
  DOCTOR_OK=1
else
  DOCTOR_OK=0
  echo "(doctor failed — may need firewall rule or WSL mirrored networking)"
fi

echo ""
echo "--- Step 2: WSL listener (mock dbt callback server) ---"
python3 "$REPO/scripts/wsl_oauth_listener.py" &
LISTENER_PID=$!
sleep 0.5

echo ""
echo "--- Step 3: mock CLI via wrap (opens auth URL through bridge) ---"
if wsl-web-auth-bridge-client wrap -- python3 "$REPO/scripts/wsl_mock_cli.py"; then
  WRAP_OK=1
else
  WRAP_OK=0
fi

# If wrap failed before opening browser, listener may still be waiting
if [[ "$WRAP_OK" -eq 0 ]]; then
  kill "$LISTENER_PID" 2>/dev/null || true
  if [[ "$DOCTOR_OK" -eq 0 ]]; then
    exit 2
  fi
  exit 1
fi

wait "$LISTENER_PID" || true
