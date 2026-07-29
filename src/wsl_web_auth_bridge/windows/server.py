from __future__ import annotations

import asyncio
import json
import logging
import secrets
import threading
import time
import uuid
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any
from urllib.parse import urlparse

from wsl_web_auth_bridge.config import ensure_windows_config
from wsl_web_auth_bridge.protocol import SessionRequest, SessionState, SessionStatus
from wsl_web_auth_bridge.windows.browser import open_url
from wsl_web_auth_bridge.windows.forwarder import run_listener
from wsl_web_auth_bridge.windows.network import should_tcp_forward

logger = logging.getLogger(__name__)

SESSION_TTL_SEC = 300


class SessionManager:
    def __init__(self) -> None:
        self._sessions: dict[str, SessionState] = {}
        self._lock = threading.Lock()
        self._loops: dict[str, tuple[asyncio.AbstractEventLoop, asyncio.Event, threading.Thread]] = {}

    def create(self, request: SessionRequest, default_wsl_host: str) -> SessionState:
        session_id = uuid.uuid4().hex
        wsl_host = request.wsl_host or default_wsl_host
        state = SessionState(
            session_id=session_id,
            port=request.port,
            url=request.url,
            wsl_host=wsl_host,
        )
        with self._lock:
            self._sessions[session_id] = state
        use_forward = should_tcp_forward(wsl_host, forward_requested=request.forward)
        state.tcp_forward = use_forward
        if use_forward:
            self._stop_forwarders_on_port(state.port, except_session=session_id)
            self._start_forwarder(state)
        elif request.forward:
            logger.info(
                "Browser-only session on port %s (skipping TCP forward; Windows cannot reach %s)",
                state.port,
                wsl_host,
            )
        try:
            open_url(request.url)
        except Exception as exc:
            state.status = SessionStatus.FAILED
            state.error = str(exc)
            if use_forward:
                self._stop_forwarder(session_id)
            raise
        return state

    def get(self, session_id: str) -> SessionState | None:
        with self._lock:
            return self._sessions.get(session_id)

    def _stop_forwarders_on_port(self, port: int, *, except_session: str | None = None) -> None:
        with self._lock:
            session_ids = [
                sid for sid, state in self._sessions.items()
                if state.port == port and sid != except_session
            ]
        for session_id in session_ids:
            self._stop_forwarder(session_id)

    def _start_forwarder(self, state: SessionState) -> None:
        stop_event = asyncio.Event()

        def _run() -> None:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                loop.run_until_complete(
                    run_listener(
                        listen_host="127.0.0.1",
                        listen_port=state.port,
                        target_host=state.wsl_host,
                        target_port=state.port,
                        stop_event=stop_event,
                    )
                )
            except OSError as exc:
                state.status = SessionStatus.FAILED
                state.error = str(exc)
                logger.exception("Forwarder failed for port %s", state.port)
            finally:
                loop.close()

        thread = threading.Thread(
            target=_run,
            name=f"wsl-auth-fwd-{state.port}",
            daemon=True,
        )
        thread.start()
        loop_placeholder = asyncio.new_event_loop()
        with self._lock:
            self._loops[state.session_id] = (loop_placeholder, stop_event, thread)

    def _stop_forwarder(self, session_id: str) -> None:
        with self._lock:
            entry = self._loops.pop(session_id, None)
        if not entry:
            return
        _, stop_event, thread = entry
        stop_event.set()
        thread.join(timeout=2.0)

    def cleanup_expired(self) -> None:
        now = time.time()
        # Sessions tracked by implicit TTL via thread lifecycle; optional future work


def default_wsl_gateway() -> str:
    # When WSL client omits host, Windows can try localhost forwarding (mirrored mode)
    # or require client to pass gateway IP from resolv.conf.
    return "127.0.0.1"


class BridgeHTTPServer:
    def __init__(self, host: str, port: int, token: str) -> None:
        self.host = host
        self.port = port
        self.token = token
        self.sessions = SessionManager()
        self._httpd: ThreadingHTTPServer | None = None

    def serve_forever(self) -> None:
        handler = _make_handler(self)
        self._httpd = ThreadingHTTPServer((self.host, self.port), handler)
        logger.info("Control API listening on http://%s:%s", self.host, self.port)
        self._httpd.serve_forever()

    def shutdown(self) -> None:
        if self._httpd:
            self._httpd.shutdown()


def _make_handler(server: BridgeHTTPServer) -> type[BaseHTTPRequestHandler]:
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, format: str, *args: Any) -> None:  # noqa: A003
            logger.debug("%s - %s", self.address_string(), format % args)

        def _unauthorized(self) -> None:
            self._json(401, {"error": "unauthorized"})

        def _json(self, status: int, payload: dict[str, Any]) -> None:
            body = json.dumps(payload).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def _read_json(self) -> dict[str, Any]:
            length = int(self.headers.get("Content-Length", "0"))
            if length <= 0:
                return {}
            raw = self.rfile.read(length)
            return json.loads(raw.decode("utf-8"))

        def _authorized(self) -> bool:
            auth = self.headers.get("Authorization", "")
            if auth == f"Bearer {server.token}":
                return True
            return secrets.compare_digest(
                self.headers.get("X-Bridge-Token", ""),
                server.token,
            )

        def do_GET(self) -> None:  # noqa: N802
            if not self._authorized():
                return self._unauthorized()
            path = urlparse(self.path).path
            if path == "/v1/health":
                return self._json(200, {"ok": True, "service": "wsl-web-auth-bridge"})
            if path.startswith("/v1/sessions/"):
                session_id = path.split("/")[-1]
                state = server.sessions.get(session_id)
                if not state:
                    return self._json(404, {"error": "session not found"})
                return self._json(200, state.to_dict())
            return self._json(404, {"error": "not found"})

        def do_POST(self) -> None:  # noqa: N802
            if not self._authorized():
                return self._unauthorized()
            path = urlparse(self.path).path
            if path != "/v1/sessions":
                return self._json(404, {"error": "not found"})
            try:
                body = self._read_json()
                request = SessionRequest.from_dict(body)
                state = server.sessions.create(request, default_wsl_gateway())
            except json.JSONDecodeError:
                return self._json(400, {"error": "invalid json"})
            except OSError as exc:
                return self._json(500, {"error": str(exc)})
            except RuntimeError as exc:
                return self._json(500, {"error": str(exc)})
            return self._json(201, state.to_dict())

    return Handler


def run_control_server(host: str = "127.0.0.1", port: int = 9877) -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    cfg = ensure_windows_config(control_port=port)
    token = cfg["token"]
    logger.info(
        "Config: %%USERPROFILE%%\\.wsl-web-auth-bridge\\config.json (readable from WSL via /mnt/c/Users/...)"
    )
    BridgeHTTPServer(host, port, token).serve_forever()
