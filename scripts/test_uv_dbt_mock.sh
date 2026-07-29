#!/usr/bin/env bash
set -euo pipefail

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
MOCK="$REPO/examples/dbt-mock"
export PATH="$HOME/.local/bin:$PATH"

cd "$MOCK"

echo "=== uv sync --extra bridge ==="
uv sync --extra bridge

if [[ ! -f .env.local ]]; then
  echo "ERROR: $MOCK/.env.local missing — copy env.example and add your Snowflake account details"
  exit 1
fi

echo ""
echo "=== doctor ==="
uv run wsl-web-auth-bridge-client doctor

echo ""
echo "=== uv run dbt debug (plain dbt + .env.bridge) ==="
uv run --env-file .env.bridge --env-file .env.local dbt debug --profiles-dir .
