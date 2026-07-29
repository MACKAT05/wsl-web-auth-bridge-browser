#!/usr/bin/env python3
"""Simulate Snowflake externalbrowser socket on WSL."""
from __future__ import annotations

import socket

PORT = 45678


def main() -> int:
    sock = socket.socket()
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind(("0.0.0.0", PORT))
    sock.listen(5)
    print(f"listening on 0.0.0.0:{PORT}", flush=True)
    conn, addr = sock.accept()
    print(f"accepted from {addr}", flush=True)
    data = conn.recv(65536)
    print(f"received {len(data)} bytes", flush=True)
    print(data[:200], flush=True)
    conn.sendall(
        b"HTTP/1.1 200 OK\r\nContent-Type: text/html\r\nContent-Length: 24\r\n\r\n"
        b"Snowflake authentication."
    )
    conn.close()
    sock.close()
    print("OK", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
