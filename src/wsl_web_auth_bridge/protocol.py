from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


DEFAULT_CONTROL_PORT = 9877
DEFAULT_CALLBACK_PORT = 45678
CONFIG_DIR_NAME = ".wsl-web-auth-bridge"

# localhost / 127.0.0.1 with optional path and query
LOCALHOST_URL_RE = re.compile(
    r"https?://(?:127\.0\.0\.1|localhost):(\d+)(/[^\s\"']*)?",
    re.IGNORECASE,
)
REDIRECT_URI_PORT_RE = re.compile(
    r"redirect_uri=[^&\s]*?%3A(\d+)%2F",
    re.IGNORECASE,
)


class SessionStatus(str, Enum):
    LISTENING = "listening"
    COMPLETED = "completed"
    FAILED = "failed"
    TIMEOUT = "timeout"


@dataclass
class SessionRequest:
    port: int
    url: str
    wsl_host: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "port": self.port,
            "url": self.url,
            "wsl_host": self.wsl_host,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> SessionRequest:
        return cls(
            port=int(data["port"]),
            url=str(data["url"]),
            wsl_host=(str(data["wsl_host"]) if data.get("wsl_host") else None),
        )


@dataclass
class SessionState:
    session_id: str
    port: int
    url: str
    wsl_host: str
    status: SessionStatus = SessionStatus.LISTENING
    error: str | None = None
    bytes_forwarded: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "session_id": self.session_id,
            "port": self.port,
            "url": self.url,
            "wsl_host": self.wsl_host,
            "status": self.status.value,
            "error": self.error,
            "bytes_forwarded": self.bytes_forwarded,
        }


def extract_callback_port(text: str) -> int | None:
    for pattern in (LOCALHOST_URL_RE, REDIRECT_URI_PORT_RE):
        match = pattern.search(text)
        if match:
            return int(match.group(1))
    return None


def parse_json_body(body: bytes) -> dict[str, Any]:
    if not body:
        return {}
    return json.loads(body.decode("utf-8"))
