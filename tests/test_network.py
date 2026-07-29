from __future__ import annotations

from unittest.mock import patch

from wsl_web_auth_bridge.windows.network import host_is_reachable, should_tcp_forward


def test_should_tcp_forward_localhost() -> None:
    assert should_tcp_forward("127.0.0.1", forward_requested=True) is False
    assert should_tcp_forward("localhost", forward_requested=True) is False


def test_should_tcp_forward_respects_flag() -> None:
    assert should_tcp_forward("10.0.0.2", forward_requested=False) is False


def test_should_tcp_forward_when_host_reachable() -> None:
    with patch("wsl_web_auth_bridge.windows.network.host_is_reachable", return_value=True):
        assert should_tcp_forward("172.29.6.180", forward_requested=True) is True


def test_should_tcp_forward_when_host_unreachable() -> None:
    with patch("wsl_web_auth_bridge.windows.network.host_is_reachable", return_value=False):
        assert should_tcp_forward("172.29.6.180", forward_requested=True) is False


def test_host_is_reachable_on_refused() -> None:
    with patch("socket.create_connection", side_effect=ConnectionRefusedError):
        assert host_is_reachable("172.29.6.180") is True


def test_host_is_reachable_on_timeout() -> None:
    with patch("socket.create_connection", side_effect=TimeoutError):
        assert host_is_reachable("172.29.6.180") is False
