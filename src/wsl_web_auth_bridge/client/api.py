from __future__ import annotations

import json
import shutil
import subprocess
import urllib.error
import urllib.request
from typing import Any

from wsl_web_auth_bridge.client.discover import is_wsl
from wsl_web_auth_bridge.config import auth_headers, control_base_url
from wsl_web_auth_bridge.protocol import SessionRequest


class BridgeError(RuntimeError):
    pass


def _request(
    method: str,
    path: str,
    body: dict[str, Any] | None = None,
    timeout: float = 30.0,
) -> dict[str, Any]:
    url = f"{control_base_url()}{path}"
    data = None
    headers = {"Accept": "application/json", **auth_headers()}
    if body is not None:
        data = json.dumps(body).encode("utf-8")
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read().decode("utf-8")
            return json.loads(raw) if raw else {}
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise BridgeError(f"Bridge HTTP {exc.code}: {detail}") from exc
    except urllib.error.URLError as exc:
        if is_wsl() and shutil.which("curl.exe"):
            try:
                return _request_via_curl_exe(method, url, headers, data, timeout)
            except BridgeError:
                pass
        raise BridgeError(
            f"Cannot reach bridge at {control_base_url()}. "
            "Start on Windows: wsl-web-auth-bridge serve"
        ) from exc


def _request_via_curl_exe(
    method: str,
    url: str,
    headers: dict[str, str],
    data: bytes | None,
    timeout: float,
) -> dict[str, Any]:
    cmd = ["curl.exe", "-sS", "-m", str(int(timeout)), "-X", method, url]
    for key, value in headers.items():
        cmd.extend(["-H", f"{key}: {value}"])
    if data is not None:
        cmd.extend(["--data-binary", "@-"])
    result = subprocess.run(
        cmd,
        input=data,
        capture_output=True,
        check=False,
    )
    if result.returncode != 0:
        detail = result.stderr.decode("utf-8", errors="replace").strip()
        raise BridgeError(detail or f"curl.exe failed with exit code {result.returncode}")
    raw = result.stdout.decode("utf-8")
    return json.loads(raw) if raw else {}


def health() -> dict[str, Any]:
    return _request("GET", "/v1/health")


def create_session(request: SessionRequest) -> dict[str, Any]:
    return _request("POST", "/v1/sessions", request.to_dict())


def get_session(session_id: str) -> dict[str, Any]:
    return _request("GET", f"/v1/sessions/{session_id}")
