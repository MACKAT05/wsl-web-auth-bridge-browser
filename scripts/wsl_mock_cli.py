#!/usr/bin/env python3
"""Mock CLI (dbt/schemachange) that opens auth URL via $BROWSER."""
from __future__ import annotations

import os
import subprocess
import sys

AUTH_URL = os.environ.get(
    "MOCK_AUTH_URL",
    "https://example.com/oauth/authorize?redirect_uri=http%3A%2F%2Flocalhost%3A45678%2Fcallback",
)


def main() -> int:
    browser = os.environ.get("BROWSER", "")
    if not browser:
        print("BROWSER not set", file=sys.stderr)
        return 1
    print(f"Opening auth URL via {browser}", flush=True)
    result = subprocess.run([browser, AUTH_URL])
    return result.returncode


if __name__ == "__main__":
    raise SystemExit(main())
