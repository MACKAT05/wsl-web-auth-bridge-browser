#!/usr/bin/env python3
import shutil
import subprocess

from wsl_web_auth_bridge.config import auth_headers, control_base_url

print("curl.exe:", shutil.which("curl.exe"))
url = control_base_url() + "/v1/health"
cmd = ["curl.exe", "-sS", "-m", "3", "-w", "\n%{http_code}", url]
for k, v in auth_headers().items():
    cmd.extend(["-H", f"{k}: {v}"])
print("cmd:", cmd)
result = subprocess.run(cmd, capture_output=True, text=True)
print("rc:", result.returncode)
print("stdout:", result.stdout)
print("stderr:", result.stderr)
