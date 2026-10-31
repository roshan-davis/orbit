# Orbit
**Many minds. One mission.** Any agent. Any role. Any model. Any project.

Orbit is a local-first desktop mission control for persistent, configurable AI agents working across your projects. This is an independent repository, separate from Atelier.

## Current state
Foundation scaffold: Tauri 2 + React/TypeScript UI, Python/FastAPI engine, SQLite-backed agent profiles, provider capability declarations, and tests. Live CLI execution, scheduling, worktree automation, and skill publishing are planned, not implemented. The UI currently lists persisted agents and shows honestly unknown provider energy; create/edit controls are a later milestone. The engine is started manually in development; packaged sidecar supervision is not implemented.

## Develop
Prerequisites: Python 3.11+, Node 22.12+ (or supported newer LTS), npm, and Rust stable plus [Tauri platform prerequisites](https://v2.tauri.app/start/prerequisites/) for desktop builds.

From the repository root:
```sh
python3.11 -m venv .venv
.venv/bin/python -m pip install -e './engine[dev]'
cp .env.example .env
# Load ORBIT_TOKEN from .env in your terminal; the server does not load .env automatically.
export ORBIT_TOKEN="$(.venv/bin/python -c 'import secrets; print(secrets.token_urlsafe(32))')"
.venv/bin/python -m uvicorn orbit_engine.app:app --host 127.0.0.1 --port 8765
```
In a second terminal:
```sh
cd apps/desktop
npm ci
npm run dev       # browser preview
# or: npm run tauri dev
```
Paste the engine token into the UI to connect; it stays only in page memory. For API exploration, use the same bearer token at `http://127.0.0.1:8765/docs`.
The default database is `.orbit/orbit.sqlite3` relative to the engine launch directory; set `ORBIT_DB` to override. No provider credentials are stored there.

For reproducible Python dependencies with [uv](https://docs.astral.sh/uv/), use `uv sync --project engine --extra dev --locked` and `uv run --project engine --extra dev --locked pytest engine/tests`. This creates `engine/.venv`; keep using one environment consistently. The pip steps above are an alternative.

## Checks
```sh
.venv/bin/python -m pytest engine/tests
cd apps/desktop
npm run build
# With Rust and platform prerequisites:
npm run tauri build -- --no-bundle
```

## Read next
- [Requirements](docs/requirements.md)
- [Architecture](docs/architecture.md)
- [Implementation phases](docs/roadmap.md)
- [Provider integration contract](docs/providers.md)
- [Claude/developer handoff](CONTRIBUTING.md)
- [Setup verification](docs/setup-status.md)

Repository: [roshan-davis/orbit](https://github.com/roshan-davis/orbit). It is public: anyone can read or clone it and propose a pull request; only authorized collaborators can push or merge. Develop changes in a separate Git worktree. No license is chosen yet; the owner should choose one before public release.
