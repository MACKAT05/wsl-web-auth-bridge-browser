from __future__ import annotations

import os
import sys

from wsl_web_auth_bridge.client.api import BridgeError, create_session
from wsl_web_auth_bridge.client.discover import default_callback_port, wsl_ip_for_forward
from wsl_web_auth_bridge.protocol import SessionRequest


def main() -> int:
    """BROWSER shim: register callback forward + open URL on Windows."""
    url = _extract_url(sys.argv[1:])
    if not url:
        print("wsl-web-auth-bridge-browser: no URL provided", file=sys.stderr)
        return 1

    port = default_callback_port()

    try:
        create_session(
            SessionRequest(
                port=port,
                url=url,
                wsl_host=wsl_ip_for_forward(),
                forward=True,
            )
        )
    except BridgeError as exc:
        print(f"wsl-web-auth-bridge-browser: {exc}", file=sys.stderr)
        return 1

    # webbrowser.open_new treats a zero exit code as success
    return 0


def _extract_url(argv: list[str]) -> str | None:
    for arg in argv:
        if arg.startswith("http://") or arg.startswith("https://"):
            return arg
    return argv[-1] if argv else None


if __name__ == "__main__":
    raise SystemExit(main())
