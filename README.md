# wsl-web-auth-bridge-browser

Forward **localhost OAuth / SSO callbacks** from a Windows browser to a process listening in WSL.

When a CLI in WSL binds `127.0.0.1:<port>` and opens a browser, the IdP redirects to **Windows** `localhost` — not WSL. This bridge listens on Windows, opens the auth URL, and **TCP-forwards** the callback to your WSL listener.

## Architecture

```
WSL app  bind 127.0.0.1:P  →  wait
       ↓  $BROWSER shim
Windows service  listen 127.0.0.1:P  →  proxy  →  WSL_HOST:P
                 open URL in browser
Browser  →  http://127.0.0.1:P/?code=...  →  forwarded to WSL
```

## Install

**On Windows** (control service):

```powershell
cd wsl-web-auth-bridge-browser
pip install -e .
wsl-web-auth-bridge serve
```

**In WSL** (client + browser shim):

```bash
pip install -e /mnt/c/Users/<you>/source/wsl-web-auth-bridge-browser
```

## Usage

### 1. Start the Windows service

```powershell
wsl-web-auth-bridge serve
```

Listens on `127.0.0.1:9877` (override with `--port`). Writes config to `%USERPROFILE%\.wsl-web-auth-bridge\config.json`.

### 2. Wrap any command in WSL

```bash
export PATH="$HOME/.local/bin:$PATH"
wsl-web-auth-bridge-client wrap -- dbt debug
wsl-web-auth-bridge-client wrap -- snow sql -q "select 1"
```

`wrap` sets:

- `BROWSER=wsl-web-auth-bridge-browser`
- `WEB_AUTH_CALLBACK_PORT` (default `45678`)
- `SF_AUTH_SOCKET_PORT` (same port, for Snowflake connector)

### 3. Or set `BROWSER` in `~/.bashrc`

```bash
export BROWSER=wsl-web-auth-bridge-browser
export WEB_AUTH_CALLBACK_PORT=45678
export SF_AUTH_SOCKET_PORT=45678
```

## Doctor

```bash
wsl-web-auth-bridge-client doctor
```

Checks Windows host reachability and service health.

## How it detects auth

1. **`$BROWSER` shim** — when a tool opens an auth URL, register `{port, url}` with the Windows service.
2. **Pinned callback port** — `WEB_AUTH_CALLBACK_PORT` / `SF_AUTH_SOCKET_PORT` / `sso_redirect_port` (via env you set).
3. **Stdout** (future) — parse `redirect_uri` / `localhost:<port>` from child output.

## Security

- Control API binds **loopback only** on Windows.
- WSL reaches it via the Windows host gateway IP.
- Optional shared token in `~/.wsl-web-auth-bridge/config.json` (readable from WSL via `/mnt/c/...`).
- For local dev machines only — not for servers or CI.

## License

MIT
