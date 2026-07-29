from __future__ import annotations

from pathlib import Path

import pytest

from wsl_web_auth_bridge.protocol import CONFIG_DIR_NAME
from wsl_web_auth_bridge.windows import wsl_config as wc


@pytest.fixture
def wsl_paths(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> tuple[Path, Path]:
    profile = tmp_path / "user"
    profile.mkdir()
    monkeypatch.setenv("USERPROFILE", str(profile))
    wslconfig = profile / wc.WSL_CONFIG_NAME
    backup = profile / CONFIG_DIR_NAME / wc.BACKUP_NAME
    return wslconfig, backup


def test_install_creates_mirrored_config(wsl_paths: tuple[Path, Path]) -> None:
    wslconfig, backup = wsl_paths
    status = wc.install_mirrored()
    assert wslconfig.is_file()
    text = wslconfig.read_text(encoding="utf-8")
    assert "networkingMode=mirrored" in text.replace(" ", "")
    assert status.is_mirrored
    assert not backup.is_file()


def test_install_backs_up_existing_config(wsl_paths: tuple[Path, Path]) -> None:
    wslconfig, backup = wsl_paths
    wslconfig.write_text("[wsl2]\nmemory=8GB\n", encoding="utf-8")
    wc.install_mirrored()
    assert backup.is_file()
    text = wslconfig.read_text(encoding="utf-8")
    assert "memory=8GB" in text
    assert "networkingMode=mirrored" in text


def test_undo_restores_backup(wsl_paths: tuple[Path, Path]) -> None:
    wslconfig, backup = wsl_paths
    wslconfig.write_text("[wsl2]\nmemory=8GB\n", encoding="utf-8")
    wc.install_mirrored()
    wc.undo_mirrored()
    assert wslconfig.read_text(encoding="utf-8") == "[wsl2]\nmemory=8GB\n"
    assert not backup.is_file()


def test_undo_removes_mirrored_when_no_backup(wsl_paths: tuple[Path, Path]) -> None:
    wslconfig, _backup = wsl_paths
    wc.install_mirrored()
    wc.undo_mirrored()
    assert not wslconfig.exists()
