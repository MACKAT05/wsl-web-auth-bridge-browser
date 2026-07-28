from __future__ import annotations

import logging
import subprocess
import webbrowser

logger = logging.getLogger(__name__)


def open_url(url: str) -> None:
    logger.info("Opening browser: %s", url[:120])
    opened = webbrowser.open(url, new=1, autoraise=True)
    if not opened:
        # Fallback for Windows
        try:
            subprocess.Popen(["cmd", "/c", "start", "", url], close_fds=True)
            return
        except OSError as exc:
            raise RuntimeError(f"Failed to open browser for {url}") from exc
