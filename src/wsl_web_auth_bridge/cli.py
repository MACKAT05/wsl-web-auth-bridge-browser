from __future__ import annotations

import argparse
import sys


def serve_main() -> None:
    if sys.platform != "win32":
        print(
            "wsl-web-auth-bridge must run on Windows (the browser + callback host).",
            file=sys.stderr,
        )
        raise SystemExit(1)

    argv = sys.argv[1:]
    if not argv or argv[0].startswith("-") or argv[0] == "serve":
        if argv and argv[0] == "serve":
            argv = argv[1:]
        _run_serve(argv)
        return

    if argv[0] == "install-mirrored":
        _run_install_mirrored(argv[1:])
        return
    if argv[0] == "undo-mirrored":
        _run_undo_mirrored(argv[1:])
        return
    if argv[0] == "networking-status":
        _run_networking_status(argv[1:])
        return

    print(f"unknown command: {argv[0]}", file=sys.stderr)
    raise SystemExit(2)


def _run_serve(argv: list[str]) -> None:
    parser = argparse.ArgumentParser(description="Windows localhost OAuth callback bridge")
    parser.add_argument("--host", default="127.0.0.1", help="Control API bind address")
    parser.add_argument("--port", type=int, default=9877, help="Control API port")
    args = parser.parse_args(argv)

    from wsl_web_auth_bridge.windows.server import run_control_server

    run_control_server(host=args.host, port=args.port)


def _run_install_mirrored(argv: list[str]) -> None:
    parser = argparse.ArgumentParser(description="Enable WSL mirrored networking in .wslconfig")
    parser.add_argument(
        "--shutdown",
        action="store_true",
        help="Run wsl --shutdown after writing config (required for WSL to pick up changes)",
    )
    args = parser.parse_args(argv)

    from wsl_web_auth_bridge.windows.wsl_config import install_mirrored, read_status

    before = read_status()
    install_mirrored(shutdown=args.shutdown)
    after = read_status()
    print(f"Wrote mirrored networking to {after.path}")
    if before.exists and before.backup_exists:
        print(f"Previous config already backed up at {after.backup_path}")
    elif before.exists:
        print(f"Backed up previous config to {after.backup_path}")
    if not args.shutdown:
        print("Restart WSL for changes to apply: wsl --shutdown")
    print("Undo with: wsl-web-auth-bridge undo-mirrored")


def _run_undo_mirrored(argv: list[str]) -> None:
    parser = argparse.ArgumentParser(description="Restore .wslconfig from backup or remove mirrored mode")
    parser.add_argument(
        "--shutdown",
        action="store_true",
        help="Run wsl --shutdown after restoring config",
    )
    args = parser.parse_args(argv)

    from wsl_web_auth_bridge.windows.wsl_config import read_status, undo_mirrored

    status = read_status()
    if not status.is_mirrored and not status.backup_exists:
        print("Mirrored networking is not enabled and no backup was found.")
        raise SystemExit(0)

    undo_mirrored(shutdown=args.shutdown)
    after = read_status()
    print(f"Restored WSL config at {after.path}")
    if not args.shutdown:
        print("Restart WSL for changes to apply: wsl --shutdown")


def _run_networking_status(argv: list[str]) -> None:
    argparse.ArgumentParser(description="Show WSL networking config status").parse_args(argv)

    from wsl_web_auth_bridge.windows.wsl_config import read_status

    status = read_status()
    print(f"  .wslconfig: {status.path}")
    print(f"  exists: {status.exists}")
    print(f"  networkingMode: {status.networking_mode or '(default)'}")
    print(f"  mirrored: {status.is_mirrored}")
    print(f"  backup: {status.backup_path if status.backup_exists else '(none)'}")


def client_main() -> None:
    parser = argparse.ArgumentParser(description="WSL client for wsl-web-auth-bridge")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("doctor", help="Check bridge connectivity")

    activate_parser = sub.add_parser(
        "activate",
        help="Print shell snippet: eval \"$(wsl-web-auth-bridge-client activate)\"",
    )
    activate_parser.add_argument(
        "--shell",
        default="bash",
        choices=("bash",),
        help="Shell dialect for activation snippet",
    )
    activate_parser.add_argument(
        "--wrap",
        default="dbt,snow,schemachange",
        help="Comma-separated commands to auto-wrap",
    )
    activate_parser.add_argument(
        "--client",
        default=None,
        help="Path to wsl-web-auth-bridge-client",
    )
    activate_parser.add_argument(
        "--env-only",
        action="store_true",
        help="Export bridge env vars only (no shell wrappers around dbt/snow)",
    )

    sub.add_parser("env", help="Print dotenv snippet for uv run / direnv (.env.bridge)")

    wrap_parser = sub.add_parser("wrap", help="Run a command with BROWSER shim and pinned callback port")
    wrap_parser.add_argument("args", nargs=argparse.REMAINDER, help="Command after --")

    args = parser.parse_args()

    if args.command == "doctor":
        from wsl_web_auth_bridge.client.wrap import run_doctor

        raise SystemExit(run_doctor())

    if args.command == "activate":
        from wsl_web_auth_bridge.client.activate import emit_bash
        import sys

        wrap_commands = tuple(c.strip() for c in args.wrap.split(",") if c.strip())
        sys.stdout.write(
            emit_bash(
                wrap_commands=wrap_commands,
                client_bin=args.client,
                env_only=args.env_only,
            )
        )
        raise SystemExit(0)

    if args.command == "env":
        from wsl_web_auth_bridge.client.activate import emit_dotenv
        import sys

        sys.stdout.write(emit_dotenv())
        raise SystemExit(0)

    if args.command == "wrap":
        from wsl_web_auth_bridge.client.wrap import run_wrap

        raise SystemExit(run_wrap(args.args))

    raise SystemExit(2)
