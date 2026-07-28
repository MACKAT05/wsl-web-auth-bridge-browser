from __future__ import annotations

import argparse
import sys


def serve_main() -> None:
    if sys.platform != "win32":
        print(
            "wsl-web-auth-bridge serve must run on Windows (the browser + callback host).",
            file=sys.stderr,
        )
        raise SystemExit(1)

    parser = argparse.ArgumentParser(description="Windows localhost OAuth callback bridge")
    parser.add_argument("--host", default="127.0.0.1", help="Control API bind address")
    parser.add_argument("--port", type=int, default=9877, help="Control API port")
    args = parser.parse_args()

    from wsl_web_auth_bridge.windows.server import run_control_server

    run_control_server(host=args.host, port=args.port)


def client_main() -> None:
    parser = argparse.ArgumentParser(description="WSL client for wsl-web-auth-bridge")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("doctor", help="Check bridge connectivity")

    wrap_parser = sub.add_parser("wrap", help="Run a command with BROWSER shim and pinned callback port")
    wrap_parser.add_argument("args", nargs=argparse.REMAINDER, help="Command after --")

    args = parser.parse_args()

    if args.command == "doctor":
        from wsl_web_auth_bridge.client.wrap import run_doctor

        raise SystemExit(run_doctor())

    if args.command == "wrap":
        from wsl_web_auth_bridge.client.wrap import run_wrap

        raise SystemExit(run_wrap(args.args))

    raise SystemExit(2)
