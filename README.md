# Orbit
**Many minds. One mission.** Any agent. Any role. Any model. Any project.

Orbit is a local-first desktop mission control for persistent, configurable AI agents working across your projects. This is an independent repository, separate from Atelier.

## Current state
Tauri 2 + React/TypeScript UI, Python/FastAPI engine and SQLite state support
persistent agents, project registration, task assignments and bounded installed-local
Ollama file runs. Select a project, create/assign a task, explicitly grant named text
files and an existing external worktree parent, then start and refresh logs/diffs.
Cancellation and restart interruption retain isolated worktrees without automatic
retry. Cloud execution, scheduling and skill publishing remain planned. Engine
startup/token entry are manual; packaged sidecar supervision is not implemented.
Open **Help** in the app for the current step-by-step guide, examples and limitations; it is available without an engine connection.
See [ORB-007 evidence and limits](docs/work-items/ORB-007.md) before using the preview.

## Run from your normal clone

Open your regular cloned repository in VS Code. Pull merged changes on `main`
and run from that folder. Contributor worktrees are for preparing PRs; they are
not required to use the app.

```sh
git pull --ff-only origin main
```

### 1. Install dependencies once

Prerequisites: Python 3.11+, [uv](https://docs.astral.sh/uv/getting-started/installation/),
Node 22.12+ (or a supported newer LTS), and npm. Native desktop development/builds
also require Rust stable and the [Tauri macOS prerequisites](https://v2.tauri.app/start/prerequisites/).
Browser development does not require Rust. From the repository root:

```sh
uv sync --project engine --extra dev --locked
npm ci --prefix apps/desktop
```

This creates `engine/.venv`. Alternatively, use a Python 3.11+ executable to create
`engine/.venv`, then install with
`engine/.venv/bin/python -m pip install -e './engine[dev]'`. Use one environment
consistently. Repeat installation when the corresponding dependency lockfile changes.

### 2. Start the engine — terminal A

From the repository root, generate a private session token without displaying it,
copy it to the macOS clipboard for the app's connection field, and start the engine:

```sh
export ORBIT_DB="$PWD/.orbit/orbit.sqlite3"
export ORBIT_TOKEN="$(engine/.venv/bin/python -c 'import secrets; print(secrets.token_urlsafe(32))')"
printf '%s' "$ORBIT_TOKEN" | pbcopy
engine/.venv/bin/python -m uvicorn orbit_engine.app:app --host 127.0.0.1 --port 8765
```

Keep this terminal running. `ORBIT_TOKEN` is the local engine session secret, not
a provider credential. Paste it only into **Workspace setup → Engine session
token**. Do not commit it or put it in missions, screenshots, logs or support messages.
The server does not load `.env` automatically. `pbcopy` is macOS-specific; on
other systems use your trusted local method to enter the same session token.

The database path above stays in this clone's ignored `.orbit` folder. Stop the
engine with **Ctrl+C**. Starting it with a new token requires reconnecting the UI.
Saved data remains in the selected database. Reloading or closing the UI clears
its memory-only connection, not the database.

### 3A. Run the web interface — terminal B

With the engine still running, open another terminal at the repository root:

```sh
npm run dev --prefix apps/desktop
```

Open [http://127.0.0.1:1420](http://127.0.0.1:1420). In **Workspace setup**, paste the
session token copied in step 2 and choose **Connect**. Register or select a project,
then open Missions and choose **Refresh tasks**. These commands do not create sample
agents or projects automatically.

Saving React/CSS changes updates the development interface. Stop Vite with
**Ctrl+C** in terminal B. If port 1420 is occupied, stop the other Orbit frontend;
the engine allows specific local origins, so choosing an arbitrary port can fail CORS.

### 3B. Run the native desktop app in development — terminal B

Use this instead of 3A. Stop the web development server first because both use
port 1420. Keep the engine in terminal A running:

```sh
cd apps/desktop
npm run tauri -- dev
```

This starts Vite and compiles/opens the native desktop window. Connect through
Workspace setup with the same engine token. Frontend saves update through Vite;
Rust changes trigger recompilation. The first native build is slower while its
dependencies compile. **Ctrl+C** in terminal B stops desktop development; stop
terminal A separately when finished.

VS Code can run these commands in its integrated terminals. A custom task or
launcher configured on one developer's machine is local convenience setup; this
repository does not currently provide a portable one-click engine supervisor or
require machine-specific artifact folders.

## Build and run a macOS app bundle

After installing the prerequisites, stop native development. From the repository
root, build the production interface and native `.app`:

```sh
cd apps/desktop
npm run tauri -- build --bundles app
open src-tauri/target/release/bundle/macos/Orbit.app
```

Tauri runs the configured frontend build, compiles the Rust desktop shell and
packages the interface assets into `Orbit.app`. The explicit `--bundles app`
requests the macOS bundle even though automatic bundling is disabled in the current
configuration. You can copy that `.app` to your Applications folder. If
`CARGO_TARGET_DIR` is set, find `release/bundle/macos/Orbit.app` under that directory
instead of `src-tauri/target`.

**The built app still needs the separately started engine from step 2.** Open
Workspace setup and connect with that engine's session token. The packaged
interface does not need Vite, but it does not bundle Python, start/stop the engine
or automatically establish its authenticated session. Closing the app does not
stop a manually started engine.

| Use | Current readiness |
| --- | --- |
| Browser/native development from a clone | Available with the commands above |
| Locally built macOS `.app` with a separately running engine | Available for local testing |
| Self-contained install-and-launch application | Not implemented yet |

A self-contained release still needs a packaged engine with managed startup and
shutdown, secure automatic session handoff, stable application-data storage,
upgrade/backup/recovery checks and clean-machine installation tests. Distribution
to other Macs also needs an appropriate signing/notarization workflow. See
[Tauri distribution](https://v2.tauri.app/distribute/) and [roadmap phase 6](docs/roadmap.md).
A successful `.app` build does not establish release readiness.

## Local model runs and troubleshooting

The interface, profiles and task metadata can be tested without model inference.
To execute a local file run, Ollama must be running locally with a supported model
already installed. A saved model name or installed-model inventory does not prove
run readiness; the engine checks it again at Start. Orbit does not download models.
Cloud CLI execution remains disabled in this preview.

- **Engine unavailable:** check terminal A and port 8765. Both frontend and engine
  must run for connected features; neither `npm run dev` nor `tauri dev` starts Python.
- **Connection denied:** use the same token configured for the current engine. A
  restarted engine may have a different token. Do not share or print it for diagnosis.
- **Port 1420 already in use:** stop the other web/native frontend or local launcher
  before switching modes. Do not start two development frontends on the same port.
- **A different empty workspace appears:** check the engine launch folder and
  `ORBIT_DB`; the database location determines which saved data loads.
- **Native build fails:** check Rust and Tauri platform prerequisites; record the
  actual error. Browser development remains a separate option.

## Checks

From the repository root:

```sh
engine/.venv/bin/python -m pytest engine/tests
npm test --prefix apps/desktop
npm run build --prefix apps/desktop
# With Rust and platform prerequisites:
npm run tauri --prefix apps/desktop -- build --no-bundle
```

## Read next
- [Requirements](docs/requirements.md)
- [Architecture](docs/architecture.md)
- [Design system and UI patterns](docs/design-system.md)
- [Implementation phases](docs/roadmap.md)
- [Provider integration contract](docs/providers.md)
- [Claude/developer handoff](CONTRIBUTING.md)
- [Setup verification](docs/setup-status.md)

Repository: [roshan-davis/orbit](https://github.com/roshan-davis/orbit). It is public: anyone can read or clone it and propose a pull request; only authorized collaborators can push or merge. Develop changes in a separate Git worktree. No license is chosen yet; the owner should choose one before public release.
