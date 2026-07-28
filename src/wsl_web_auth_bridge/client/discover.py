from __future__ import annotations

import os
import re
from pathlib import Path


def windows_host_ip() -> str:
    override = os.environ.get("WSL_WEB_AUTH_BRIDGE_HOST")
    if override:
        return override
    resolv = Path("/etc/resolv.conf")
    if resolv.is_file():
        for line in resolv.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line.startswith("nameserver"):
                parts = line.split()
                if len(parts) >= 2 and parts[1] not in ("127.0.0.1", "::1"):
                    return parts[1]
    # Fallback documented for Docker Desktop / some setups
    return "host.docker.internal"


def is_wsl() -> bool:
    if os.environ.get("WSL_DISTRO_NAME"):
        return True
    try:
        with open("/proc/version", encoding="utf-8") as fh:
            return "microsoft" in fh.read().lower()
    except OSError:
        return False


def wsl_ip_for_forward() -> str:
    """WSL VM IP reachable from Windows (listener should bind 0.0.0.0)."""
    import subprocess

    try:
        result = subprocess.run(
            ["hostname", "-I"],
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode == 0:
            ips = result.stdout.strip().split()
            if ips:
                return ips[0]
    except OSError:
        pass
    return windows_host_ip()


def default_callback_port() -> int:
    for key in (
        "WEB_AUTH_CALLBACK_PORT",
        "SF_AUTH_SOCKET_PORT",
        "SNOWFLAKE_AUTH_SOCKET_PORT",
    ):
        raw = os.environ.get(key)
        if raw and raw.isdigit():
            return int(raw)
    return 45678


def callback_port_env() -> dict[str, str]:
    port = str(default_callback_port())
    return {
        "WEB_AUTH_CALLBACK_PORT": port,
        "SF_AUTH_SOCKET_PORT": port,
        # Allow Windows-side TCP proxy to reach the WSL listener.
        "SF_AUTH_SOCKET_ADDR": "0.0.0.0",
    }
