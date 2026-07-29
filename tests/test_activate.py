from __future__ import annotations

from wsl_web_auth_bridge.client.activate import activation_env, bridge_env, emit_bash, emit_dotenv


def test_activation_env_sets_browser() -> None:
    env = activation_env()
    assert "BROWSER" in env
    assert env["WSL_WEB_AUTH_BRIDGE_ACTIVE"] == "1"
    assert env["SF_AUTH_SOCKET_ADDR"] == "0.0.0.0"
    assert env["WEB_AUTH_CALLBACK_PORT"] == "45679"


def test_bridge_env_omits_active_flag() -> None:
    env = bridge_env()
    assert "BROWSER" in env
    assert "WSL_WEB_AUTH_BRIDGE_ACTIVE" not in env


def test_emit_dotenv() -> None:
    dotenv = emit_dotenv()
    assert "BROWSER=" in dotenv
    assert "WEB_AUTH_CALLBACK_PORT=45679" in dotenv


def test_emit_bash_wraps_dbt() -> None:
    script = emit_bash(wrap_commands=("dbt",), client_bin="/bin/wsl-web-auth-bridge-client")
    assert "export BROWSER=" in script
    assert "dbt() { /bin/wsl-web-auth-bridge-client wrap -- command dbt" in script
    assert "wsl-web-auth-bridge-deactivate()" in script


def test_emit_bash_env_only() -> None:
    script = emit_bash(env_only=True)
    assert "export BROWSER=" in script
    assert "dbt() {" not in script
    assert "wsl-web-auth-bridge-deactivate()" in script
