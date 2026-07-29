from __future__ import annotations

import socket


def host_is_reachable(host: str, timeout: float = 0.5) -> bool:
    """Return True when Windows can open a TCP connection to host (port closed is OK)."""
    try:
        with socket.create_connection((host, 1), timeout=timeout):
            return True
    except ConnectionRefusedError:
        return True
    except OSError as exc:
        # WinError 10061: connection refused — host is reachable
        if getattr(exc, "winerror", None) == 10061:
            return True
        return False


def should_tcp_forward(wsl_host: str, *, forward_requested: bool) -> bool:
    if not forward_requested:
        return False
    if wsl_host in {"127.0.0.1", "localhost", "::1"}:
        return False
    return host_is_reachable(wsl_host)
