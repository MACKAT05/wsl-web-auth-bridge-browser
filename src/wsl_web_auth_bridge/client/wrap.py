from __future__ import annotations

import os
import shutil
import subprocess
import sys

from wsl_web_auth_bridge.client.api import BridgeError, health
from wsl_web_auth_bridge.client.discover import (
    callback_port_env,
    is_wsl,
    localhost_is_shared,
    needs_tcp_forward,
    windows_host_ip,
)


def run_doctor() -> int:
    print("wsl-web-auth-bridge doctor")
    print(f"  WSL detected: {is_wsl()}")
    print(f"  Windows host IP: {windows_host_ip()}")
    print(f"  Localhost shared: {localhost_is_shared()}")
    print(f"  TCP forward (client hint): {needs_tcp_forward()}")
    try:
        info = health()
        print(f"  Bridge health: OK ({info})")
    except BridgeError as exc:
        print(f"  Bridge health: FAIL — {exc}")
        return 1
    cfg_path = os.environ.get("WSL_WEB_AUTH_BRIDGE_CONFIG", "")
    print(f"  Callback port env: {callback_port_env()}")
    if cfg_path:
        print(f"  Config path: {cfg_path}")
    return 0


def run_wrap(argv: list[str]) -> int:
    if not argv or argv[0] != "--":
        print("Usage: wsl-web-auth-bridge-client wrap -- <command> [args...]", file=sys.stderr)
        return 2

    command = argv[1:]
    if not command:
        print("wrap: missing command after --", file=sys.stderr)
        return 2

    env = os.environ.copy()
    env.update(callback_port_env())
    shim = shutil.which("wsl-web-auth-bridge-browser")
    if shim:
        env["BROWSER"] = shim
    else:
        env["BROWSER"] = "wsl-web-auth-bridge-browser"

    try:
        health()
    except BridgeError as exc:
        print(f"wrap: {exc}", file=sys.stderr)
        return 1

    completed = subprocess.run(command, env=env)
    return completed.returncode
