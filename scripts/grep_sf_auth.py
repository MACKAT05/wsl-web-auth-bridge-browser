#!/usr/bin/env python3
import importlib.util
import pathlib
import sys

spec = importlib.util.find_spec("snowflake.connector")
if not spec or not spec.origin:
    sys.exit("snowflake-connector-python is not installed")
root = pathlib.Path(spec.origin).parent
for path in root.rglob("*.py"):
    text = path.read_text(encoding="utf-8", errors="replace")
    if "AUTH_SOCKET" in text:
        for i, line in enumerate(text.splitlines(), 1):
            if "AUTH_SOCKET" in line:
                print(f"{path.name}:{i}: {line.strip()}")
