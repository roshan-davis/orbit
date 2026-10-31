# Phased implementation

| Phase | Deliverables | Exit gate |
| --- | --- | --- |
| 0 — Foundation (this setup) | Independent Git repository, docs, desktop shell, SQLite agent API, provider declarations, tests | API tests and UI build pass; native-build limitations recorded |
| 1 — One safe local mission | Project registry, agent editing, task state machine, Git worktree manager, Ollama adapter, logs/cancellation | A task runs against a temporary repo, survives failures, produces a reviewed diff; no main-checkout mutation |
| 2 — Subscription CLI support | Independently validate Claude Code, Codex CLI, Gemini CLI sign-in/machine output, capability detection and process handling | Contract tests with fixtures, opt-in real smoke tests per installed CLI; missing subscription auth fails closed, no API fallback |
| 3 — Team orchestration | Dynamic assignments, dependency queue, peer review, human approvals, restart recovery | Two independent agents implement/review; rejection and conflicts block merge; duplicate/restart tests pass |
| 4 — Energy and scheduling | Shared account pools, windows, stale/unknown observations, reserves, local compute | Shared agents never double-count pools; short/long limits and unknown states tested |
| 5 — Skill evolution | Periodic observer, architect proposals, evaluations, independent review, approval and registry | Unapproved version cannot activate; regression rollback demonstrated; skill/knowledge/automation classification |
| 6 — Desktop distribution | Managed Python sidecar, secure token bootstrap, migration backups, packaging/signing | Clean-machine install, lifecycle, upgrade/restore and accessibility validation |
| 7 — Private multi-device access | Device pairing, encrypted private transport, scoped permissions, remote dashboard | Unauthorized/revoked devices denied; remote approval audit and reconnect tested |
| 8 — Design integrations | Google Stitch / Claude design discovery and supported connectors | Verified access and cost policy, artifact round-trip, accessibility and design-to-code review |

## First tasks for Claude and Codex
1. Add agent create/edit controls against the existing API and define shared API contract generation.
2. Implement project registration and safe worktree lifecycle using temporary Git repositories in tests.
3. Define task/assignment migrations and atomic transition tests before starting workers.
4. Implement Ollama discovery without pulling models or spending cloud quota.
5. Investigate CLI subscription preflight and fixtures one provider at a time; do not enable execution from a binary-presence check alone.

Keep each task on a focused branch with explicit acceptance criteria and independent review. Phases describe release gates; foundation declarations are not completed runtime adapters.
