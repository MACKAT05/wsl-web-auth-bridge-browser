from __future__ import annotations

import os
import re
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path

from wsl_web_auth_bridge.protocol import CONFIG_DIR_NAME

WSL_CONFIG_NAME = ".wslconfig"
WSL_SECTION = "wsl2"
MIRRORED_MODE = "mirrored"
NETWORKING_MODE_KEY = "networkingMode"
BACKUP_NAME = "wslconfig.backup"
_SECTION_RE = re.compile(r"^\s*\[([^\]]+)\]\s*$")
_KV_RE = re.compile(r"^\s*([^=]+?)\s*=\s*(.*?)\s*$")


@dataclass
class WslConfigStatus:
    path: Path
    exists: bool
    networking_mode: str | None
    backup_exists: bool
    backup_path: Path

    @property
    def is_mirrored(self) -> bool:
        return (self.networking_mode or "").lower() == MIRRORED_MODE


def wslconfig_path() -> Path:
    return Path(os.environ.get("USERPROFILE", Path.home())) / WSL_CONFIG_NAME


def backup_path() -> Path:
    return Path(os.environ.get("USERPROFILE", Path.home())) / CONFIG_DIR_NAME / BACKUP_NAME


def read_status() -> WslConfigStatus:
    path = wslconfig_path()
    mode = _read_networking_mode(path) if path.is_file() else None
    backup = backup_path()
    return WslConfigStatus(
        path=path,
        exists=path.is_file(),
        networking_mode=mode,
        backup_exists=backup.is_file(),
        backup_path=backup,
    )


def install_mirrored(*, shutdown: bool = False) -> WslConfigStatus:
    if os.name != "nt":
        raise RuntimeError("install-mirrored must run on Windows")

    path = wslconfig_path()
    backup = backup_path()
    backup.parent.mkdir(parents=True, exist_ok=True)

    if path.is_file() and not backup.is_file():
        shutil.copy2(path, backup)

    content = path.read_text(encoding="utf-8") if path.is_file() else ""
    path.write_text(_set_wsl2_option(content, NETWORKING_MODE_KEY, MIRRORED_MODE), encoding="utf-8")

    status = read_status()
    if shutdown:
        _wsl_shutdown()
    return status


def undo_mirrored(*, shutdown: bool = False) -> WslConfigStatus:
    if os.name != "nt":
        raise RuntimeError("undo-mirrored must run on Windows")

    path = wslconfig_path()
    backup = backup_path()

    if backup.is_file():
        shutil.copy2(backup, path)
        backup.unlink()
    elif path.is_file():
        content = _remove_wsl2_option(path.read_text(encoding="utf-8"), NETWORKING_MODE_KEY)
        if content.strip():
            path.write_text(content, encoding="utf-8")
        else:
            path.unlink()

    status = read_status()
    if shutdown:
        _wsl_shutdown()
    return status


def _read_networking_mode(path: Path) -> str | None:
    in_wsl2 = False
    for line in path.read_text(encoding="utf-8").splitlines():
        section = _SECTION_RE.match(line)
        if section:
            in_wsl2 = section.group(1).strip().lower() == WSL_SECTION
            continue
        if not in_wsl2:
            continue
        match = _KV_RE.match(line)
        if match and match.group(1).strip().lower() == NETWORKING_MODE_KEY.lower():
            return match.group(2).strip()
    return None


def _set_wsl2_option(content: str, key: str, value: str) -> str:
    lines = content.splitlines()
    out: list[str] = []
    in_wsl2 = False
    wsl2_seen = False
    replaced = False
    key_lower = key.lower()

    for line in lines:
        section = _SECTION_RE.match(line)
        if section:
            if in_wsl2 and not replaced:
                out.append(f"{key}={value}")
                replaced = True
            in_wsl2 = section.group(1).strip().lower() == WSL_SECTION
            if in_wsl2:
                wsl2_seen = True
            out.append(line)
            continue
        if in_wsl2:
            match = _KV_RE.match(line)
            if match and match.group(1).strip().lower() == key_lower:
                out.append(f"{key}={value}")
                replaced = True
                continue
        out.append(line)

    if in_wsl2 and not replaced:
        out.append(f"{key}={value}")
        replaced = True

    if not wsl2_seen:
        if out and out[-1].strip():
            out.append("")
        out.extend([f"[{WSL_SECTION}]", f"{key}={value}"])

    text = "\n".join(out)
    if text and not text.endswith("\n"):
        text += "\n"
    return text


def _remove_wsl2_option(content: str, key: str) -> str:
    lines = content.splitlines()
    out: list[str] = []
    in_wsl2 = False
    wsl2_start: int | None = None
    key_lower = key.lower()

    for line in lines:
        section = _SECTION_RE.match(line)
        if section:
            in_wsl2 = section.group(1).strip().lower() == WSL_SECTION
            if in_wsl2:
                wsl2_start = len(out)
            out.append(line)
            continue
        if in_wsl2:
            match = _KV_RE.match(line)
            if match and match.group(1).strip().lower() == key_lower:
                continue
            if not line.strip():
                continue
        out.append(line)

    if wsl2_start is not None:
        section_lines = out[wsl2_start:]
        if len(section_lines) == 1 and section_lines[0].strip() == f"[{WSL_SECTION}]":
            out = out[:wsl2_start]

    while out and not out[-1].strip():
        out.pop()

    text = "\n".join(out)
    if text and not text.endswith("\n"):
        text += "\n"
    return text


def _wsl_shutdown() -> None:
    subprocess.run(["wsl", "--shutdown"], check=False)
