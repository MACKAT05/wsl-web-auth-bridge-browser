#!/usr/bin/env python3
"""Simulate IdP redirect hitting Windows localhost callback port."""
from __future__ import annotations

import socket
import sys

PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 45678
CODE = sys.argv[2] if len(sys.argv) > 2 else "dbt-smoke-test"


def main() -> int:
    request = (
        f"GET /callback?code={CODE}&state=xyz HTTP/1.1\r\n"
        f"Host: localhost:{PORT}\r\n"
        "\r\n"
    ).encode()
    with socket.create_connection(("127.0.0.1", PORT), timeout=10) as client:
        client.sendall(request)
        response = client.recv(4096)
    print(response.decode("utf-8", errors="replace"))
    return 0 if b"200" in response else 1


if __name__ == "__main__":
    raise SystemExit(main())
