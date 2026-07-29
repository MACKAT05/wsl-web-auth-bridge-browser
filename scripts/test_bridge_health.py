#!/usr/bin/env python3
from wsl_web_auth_bridge.config import auth_headers, config_path, load_config
from wsl_web_auth_bridge.client.api import health

p = config_path()
print("config_path:", p, "exists:", p.is_file())
print("token_prefix:", (load_config().get("token") or "")[:8])
print("auth_headers:", bool(auth_headers()))
try:
    print("health:", health())
except Exception as exc:
    print("health_error:", exc)
