from __future__ import annotations

import sys

from wsl_web_auth_bridge.client.wrap import run_wrap


def exec_main() -> None:
    """uv run --group bridge wsl-web-auth-bridge-exec -- dbt debug ..."""
    raise SystemExit(run_wrap(["--", *sys.argv[1:]]))


def dbt_main() -> None:
    """uv run --group bridge wsl-web-auth-bridge-dbt debug --profiles-dir ."""
    raise SystemExit(run_wrap(["--", "dbt", *sys.argv[1:]]))


def snow_main() -> None:
    raise SystemExit(run_wrap(["--", "snow", *sys.argv[1:]]))


def schemachange_main() -> None:
    raise SystemExit(run_wrap(["--", "schemachange", *sys.argv[1:]]))
