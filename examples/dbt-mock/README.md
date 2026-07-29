# dbt smoke test

Minimal dbt project for testing `wsl-web-auth-bridge` with Snowflake `externalbrowser` auth.

## Setup

**Windows** — start the bridge:

```powershell
wsl-web-auth-bridge serve --port 9877
```

**WSL** — configure Snowflake env vars and install deps with [uv](https://docs.astral.sh/uv/):

```bash
cd examples/dbt-mock
cp env.example .env.local
# edit .env.local with your Snowflake account details
uv sync --extra bridge
```

`--extra bridge` installs `wsl-web-auth-bridge-browser` as an optional dependency (same as `uv sync --group bridge`).

## Run plain `dbt` (recommended)

`wrap` only sets `BROWSER` and callback ports. After syncing the bridge extra, load `.env.bridge` and run dbt normally:

```bash
# once per shell (or use direnv — see .envrc)
set -a && source .env.bridge && source .env.local && set +a

uv run dbt debug --profiles-dir .
```

With [direnv](https://direnv.net/), `direnv allow` loads `.env.bridge` and `.env.local` automatically, so this is enough:

```bash
uv run dbt debug --profiles-dir .
```

Without direnv, you can pass env files to uv directly:

```bash
uv run --env-file .env.bridge --env-file .env.local dbt debug --profiles-dir .
```

Regenerate `.env.bridge` after changing callback port defaults:

```bash
wsl-web-auth-bridge-client env > .env.bridge
```

## Alternative: wrapper entry points

If you prefer not to manage env files:

```bash
uv run --extra bridge wsl-web-auth-bridge-dbt debug --profiles-dir .
```

## Run with shell activate (any workflow)

Env-only (plain `dbt`):

```bash
eval "$(wsl-web-auth-bridge-client activate --env-only)"
dbt debug --profiles-dir .
```

Or shell wrappers around each CLI:

```bash
eval "$(wsl-web-auth-bridge-client activate --wrap dbt)"
dbt debug --profiles-dir .
wsl-web-auth-bridge-deactivate
```

## Downstream dbt project pattern

Add to your project's `pyproject.toml`:

```toml
[project.optional-dependencies]
bridge = ["wsl-web-auth-bridge-browser"]

[tool.uv.sources]
wsl-web-auth-bridge-browser = { path = "/path/to/wsl-web-auth-bridge-browser", editable = true }

[dependency-groups]
bridge = ["wsl-web-auth-bridge-browser"]

[tool.uv]
default-groups = []
```

Then copy `.env.bridge` (or run `wsl-web-auth-bridge-client env > .env.bridge`) and:

```bash
uv sync --extra bridge
uv run --env-file .env.bridge dbt debug
```
