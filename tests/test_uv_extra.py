from __future__ import annotations

from unittest.mock import patch

from wsl_web_auth_bridge.client import uv_extra


def test_dbt_main_wraps_dbt_argv() -> None:
    with patch("wsl_web_auth_bridge.client.uv_extra.run_wrap", return_value=0) as run_wrap:
        with patch.object(uv_extra.sys, "argv", ["wsl-web-auth-bridge-dbt", "debug", "--profiles-dir", "."]):
            with patch.object(uv_extra, "run_wrap", run_wrap):
                try:
                    uv_extra.dbt_main()
                except SystemExit as exc:
                    assert exc.code == 0
    run_wrap.assert_called_once_with(["--", "dbt", "debug", "--profiles-dir", "."])
