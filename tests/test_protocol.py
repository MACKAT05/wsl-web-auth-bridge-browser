from __future__ import annotations

from wsl_web_auth_bridge.protocol import LOCALHOST_URL_RE, extract_callback_port


def test_extract_port_from_localhost_url() -> None:
    assert extract_callback_port("Open http://127.0.0.1:45678/?token=abc") == 45678
    assert extract_callback_port("redirect to http://localhost:8000/oauth/callback") == 8000


def test_extract_port_from_redirect_uri() -> None:
    text = (
        "https://accounts.google.com/o/oauth2/auth?"
        "redirect_uri=http%3A%2F%2Flocalhost%3A42335%2Foauth2callback"
    )
    assert extract_callback_port(text) == 42335


def test_localhost_regex() -> None:
    match = LOCALHOST_URL_RE.search("http://127.0.0.1:34541/?code=x")
    assert match
    assert match.group(1) == "34541"
