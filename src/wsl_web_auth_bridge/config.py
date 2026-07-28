from __future__ import annotations

import json
import os
import secrets
import sys
from pathlib import Path

from wsl_web_auth_bridge.protocol import CONFIG_DIR_NAME, DEFAULT_CONTROL_PORT


def windows_config_dir() -> Path:
    return Path(os.environ.get("USERPROFILE", Path.home())) / CONFIG_DIR_NAME


def wsl_config_path_from_windows() -> Path | None:
    """Path readable from WSL via /mnt/c/..."""
    if sys.platform != "win32":
        return None
    home = os.environ.get("USERPROFILE", "")
    if not home or len(home) < 3 or home[1] != ":":
        return None
    drive = home[0].lower()
    rest = home[2:].replace("\\", "/")
    return Path(f"/mnt/{drive}{rest}") / CONFIG_DIR_NAME / "config.json"


def load_config() -> dict:
    path = config_path()
    if not path.is_file():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def config_path() -> Path:
    if sys.platform == "win32":
        return windows_config_dir() / "config.json"
    # WSL: prefer Windows-side config
    win_user = os.environ.get("WSL_WEB_AUTH_BRIDGE_WIN_USER")
    if win_user:
        return Path(f"/mnt/c/Users/{win_user}") / CONFIG_DIR_NAME / "config.json"
    # Heuristic: first user dir with config
    users = Path("/mnt/c/Users")
    if users.is_dir():
        for entry in sorted(users.iterdir()):
            candidate = entry / CONFIG_DIR_NAME / "config.json"
            if candidate.is_file():
                return candidate
    return Path.home() / CONFIG_DIR_NAME / "config.json"


def ensure_windows_config(control_port: int = DEFAULT_CONTROL_PORT) -> dict:
    directory = windows_config_dir()
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / "config.json"
    if path.is_file():
        data = json.loads(path.read_text(encoding="utf-8"))
        data.setdefault("control_port", control_port)
        data.setdefault("token", secrets.token_urlsafe(32))
        path.write_text(json.dumps(data, indent=2), encoding="utf-8")
        return data
    data = {
        "control_port": control_port,
        "token": secrets.token_urlsafe(32),
        "version": 1,
    }
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")
    return data


def control_base_url() -> str:
    override = os.environ.get("WSL_WEB_AUTH_BRIDGE_URL")
    if override:
        return override.rstrip("/")
    cfg = load_config()
    port = int(cfg.get("control_port", DEFAULT_CONTROL_PORT))
    if sys.platform == "win32":
        return f"http://127.0.0.1:{port}"
    from wsl_web_auth_bridge.client.discover import windows_host_ip

    host = windows_host_ip()
    return f"http://{host}:{port}"


def auth_headers() -> dict[str, str]:
    cfg = load_config()
    token = cfg.get("token") or os.environ.get("WSL_WEB_AUTH_BRIDGE_TOKEN", "")
    if not token:
        return {}
    return {"Authorization": f"Bearer {token}"}
