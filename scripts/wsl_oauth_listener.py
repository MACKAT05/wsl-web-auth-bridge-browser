#!/usr/bin/env python3
"""Mock dbt/schemachange OAuth callback listener in WSL."""
from __future__ import annotations

import os
import socket
import sys

PORT = int(os.environ.get("WEB_AUTH_CALLBACK_PORT", "45678"))


def main() -> int:
    sock = socket.socket()
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind(("0.0.0.0", PORT))
    sock.listen(1)
    print(f"WSL listener ready on 0.0.0.0:{PORT}", flush=True)

    conn, addr = sock.accept()
    data = conn.recv(8192)
    print(f"Connection from {addr}", flush=True)
    print(data.decode("utf-8", errors="replace"), flush=True)

    conn.sendall(b"HTTP/1.1 200 OK\r\nContent-Length: 2\r\n\r\nok")
    conn.close()
    sock.close()

    if b"code=" in data or b"token=" in data:
        print("OAUTH_CALLBACK_OK", flush=True)
        return 0
    print("OAUTH_CALLBACK_MISSING_CODE", flush=True)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
