#!/usr/bin/env python3
import shutil
import subprocess

print("which curl.exe:", shutil.which("curl.exe"))
print("PATH:", __import__("os").environ.get("PATH", "")[:200])
