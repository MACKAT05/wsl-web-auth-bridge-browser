#!/usr/bin/env bash
set -eu
export PATH="$HOME/.local/bin:$PATH"
echo "=== doctor ==="
wsl-web-auth-bridge-client doctor
echo ""
echo "=== dbt ==="
which dbt || true
dbt --version 2>/dev/null | head -1 || true
echo ""
echo "=== wrap dbt debug ==="
wsl-web-auth-bridge-client wrap -- dbt debug
