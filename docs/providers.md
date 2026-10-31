# Provider policy and integration contract

Cloud execution must use the user's supported native CLI account/subscription login. Orbit must never substitute an API key, direct API request, Vertex/Bedrock route, or paid API fallback. If the provider or plan does not support the requested flow, mark it unsupported. Authentication, licensing and supported automation must be verified per installed CLI version before enabling execution. Never extract, relay or reuse a provider's OAuth token outside that CLI.

| Provider | Intended route | Foundation status |
| --- | --- | --- |
| Claude | Installed Claude Code with supported subscription sign-in | Declaration only; execution disabled |
| Codex | Installed Codex CLI with supported account/subscription sign-in | Declaration only; execution disabled |
| Gemini | Installed Gemini CLI with eligible Google account sign-in | Declaration only; execution disabled |
| Ollama | Local loopback service, installed Gemma/Qwen models | Declaration only; no download or execution |

A Google account login is not proof of a particular subscription entitlement. Provider quotas and features vary; no fixed quota percentages or reset schedules are promised. Claude subscription OAuth is for native Claude Code use; invoking the official CLI does not authorize arbitrary token reuse. Confirm the intended orchestration mode is supported before phase 2.

Adapter contract (planned): `discover()`, `check_auth()`, `capabilities()`, `start(assignment)`, `events(run)`, `cancel(run)`, `observe_usage()`. Discovery reports installed version; it must not claim authenticated readiness. Default auth is unknown and default execution disabled. Normalize failures separately: missing binary, unauthenticated, unsupported auth, quota exhausted, timeout, cancelled and provider failure. Never automatically switch account/provider or spend money after failure.

Integration tests must use fake subprocesses and recorded sanitized fixtures by default. Real sign-in and model runs are opt-in and must never run in CI. Do not automate interactive login or log prompts/tokens. Local models report local compute availability, not fictional subscription quota.

## Primary references
Reviewed during setup, October 31, 2026; recheck before implementation:
- [Claude Code legal and compliance](https://code.claude.com/docs/en/legal-and-compliance)
- [Gemini CLI authentication](https://geminicli.com/docs/get-started/authentication/)
- [Tauri 2 configuration](https://v2.tauri.app/reference/config/)
- [FastAPI testing](https://fastapi.tiangolo.com/tutorial/testing/)

Codex CLI subscription preflight and exact command contracts remain explicit phase-2 research; no unverified command flags are baked into this scaffold.
