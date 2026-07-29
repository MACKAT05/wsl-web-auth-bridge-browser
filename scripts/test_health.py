#!/usr/bin/env python3
import shutil
from wsl_web_auth_bridge.client.api import health

print("curl.exe:", shutil.which("curl.exe"))
print("health:", health())
