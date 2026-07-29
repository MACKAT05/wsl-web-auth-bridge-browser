from __future__ import annotations

import os
import shlex
import shutil
import sys

from wsl_web_auth_bridge.client.discover import callback_port_env

DEFAULT_WRAP_COMMANDS = ("dbt", "snow", "schemachange")


def bridge_env(*, mark_active: bool = False) -> dict[str, str]:
    """Env vars needed for plain ``dbt`` / ``snow`` without ``wrap``."""
    env = callback_port_env()
    shim = shutil.which("wsl-web-auth-bridge-browser") or "wsl-web-auth-bridge-browser"
    env["BROWSER"] = shim
    if not os.environ.get("WEB_AUTH_CALLBACK_PORT"):
        env["WEB_AUTH_CALLBACK_PORT"] = os.environ.get(
            "WSL_WEB_AUTH_BRIDGE_CALLBACK_PORT", "45679"
        )
        env["SF_AUTH_SOCKET_PORT"] = env["WEB_AUTH_CALLBACK_PORT"]
    if mark_active:
        env["WSL_WEB_AUTH_BRIDGE_ACTIVE"] = "1"
    return env


def activation_env() -> dict[str, str]:
    return bridge_env(mark_active=True)


def emit_dotenv() -> str:
    lines = ["# wsl-web-auth-bridge - use with: set -a && source .env.bridge && set +a"]
    for key, value in bridge_env().items():
        lines.append(f"{key}={value}")
    return "\n".join(lines) + "\n"


def emit_bash(
    *,
    wrap_commands: tuple[str, ...] = DEFAULT_WRAP_COMMANDS,
    client_bin: str | None = None,
    env_only: bool = False,
) -> str:
    client = client_bin or shutil.which("wsl-web-auth-bridge-client") or "wsl-web-auth-bridge-client"
    lines = [
        "# wsl-web-auth-bridge activation — eval: eval \"$(wsl-web-auth-bridge-client activate)\"",
    ]
    for key, value in activation_env().items():
        lines.append(f"export {key}={shlex.quote(value)}")

    if env_only:
        lines.append(
            'echo "wsl-web-auth-bridge: env active (plain dbt/snow work; run deactivate to undo)"'
        )
        lines.append("wsl-web-auth-bridge-deactivate() {")
        lines.append(
            "  unset WSL_WEB_AUTH_BRIDGE_ACTIVE BROWSER WEB_AUTH_CALLBACK_PORT "
            "SF_AUTH_SOCKET_PORT SF_AUTH_SOCKET_ADDR"
        )
        lines.append("}")
        return "\n".join(lines) + "\n"

    for cmd in wrap_commands:
        lines.append(
            f"{cmd}() {{ {shlex.quote(client)} wrap -- command {cmd} \"$@\"; }}"
        )

    deactivate_lines = [
        "unset WSL_WEB_AUTH_BRIDGE_ACTIVE BROWSER WEB_AUTH_CALLBACK_PORT SF_AUTH_SOCKET_PORT SF_AUTH_SOCKET_ADDR",
    ]
    for cmd in wrap_commands:
        deactivate_lines.append(f"unset -f {cmd} 2>/dev/null || true")
    lines.append("wsl-web-auth-bridge-deactivate() {")
    lines.extend(f"  {line}" for line in deactivate_lines)
    lines.append("}")
    lines.append('echo "wsl-web-auth-bridge: active (run wsl-web-auth-bridge-deactivate to undo)"')
    return "\n".join(lines) + "\n"


def activate_main() -> None:
    """Console entry: print bash activation snippet to stdout."""
    raise SystemExit(run_activate(sys.argv[1:]))


def env_main() -> None:
    """Console entry: print dotenv lines for uv / direnv."""
    sys.stdout.write(emit_dotenv())
    raise SystemExit(0)


def run_activate(argv: list[str]) -> int:
    parser = __import__("argparse").ArgumentParser(
        description="Print shell snippet to activate bridge-wrapped CLI commands",
    )
    parser.add_argument(
        "--shell",
        default="bash",
        choices=("bash",),
        help="Shell dialect for activation snippet",
    )
    parser.add_argument(
        "--wrap",
        default=",".join(DEFAULT_WRAP_COMMANDS),
        help="Comma-separated commands to wrap (default: dbt,snow,schemachange)",
    )
    parser.add_argument(
        "--client",
        default=None,
        help="Path to wsl-web-auth-bridge-client (default: from PATH)",
    )
    parser.add_argument(
        "--env-only",
        action="store_true",
        help="Export bridge env vars only (no shell wrappers around dbt/snow)",
    )
    args = parser.parse_args(argv)

    wrap_commands = tuple(c.strip() for c in args.wrap.split(",") if c.strip())
    if args.shell == "bash":
        sys.stdout.write(
            emit_bash(
                wrap_commands=wrap_commands,
                client_bin=args.client,
                env_only=args.env_only,
            )
        )
        return 0
    print(f"unsupported shell: {args.shell}", file=sys.stderr)
    return 2
