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


## Local folder/action track (planned; coordinated after ORB-010)

This track can deliver useful local work before phases 2–5. It does not assert
Phase 1 acceptance: Main still coordinates a full connected desktop mission and
owned engine startup/connection work separately. Only ORB-010 documentation is
launched here. The bounded items below are proposals, not reserved ORB IDs or
implementation authorization; select unused IDs against live work/PRs when launched.

| Sequence | Bounded PR scope | Dependencies | Acceptance / boundary |
| --- | --- | --- | --- |
| F1 | Typed workspace migration/registration, minimal versioned registry and direct metadata inventory/report slice | ORB-010; existing project persistence/path services | Non-Git folder registers/restarts and inventories explicit bounded file selection without `.git` or source writes; view/export report as a run artifact; schema/handler/scope rejection and Git regression checks. Export to a user folder waits for F2. No document-body parsing or model needed. |
| F2 | One new-artifact action (supported plain-text index/report), staged publication | F1 | Explicit destination/format, no-clobber collision policy, preview/approval, destination recheck, interrupted-publication evidence/recovery. Source contents unchanged; no moves/replacements. |
| F3 | Versioned workflow templates over F1/F2 actions, direct invocation | F1–F2 | Pinned versions, typed mappings/dependencies, invalid graph/version rejection, exact run snapshot and approval boundaries; direct repeatable report flow without model. |
| F4 | Installed-local intent/entity resolver and clarification UI | F3; installed-model discovery/capability checks | Representative known/ambiguous/unsupported fixtures; schema validation independent of model; unavailable routing/direct fallback; no native tool assumption, downloads or cloud/API fallback. |
| F5 | One previewed rename/move action with recovery | F2–F4; documented crash-safe manifest protocol | Preview mappings; explicit approval; collision/source/destination-version checks; cancel/restart/partial-failure reconciliation and separately approved recovery preserve unrelated changes. No arbitrary delete/replacement action bundled. |

Each slice owns its engine contracts, persistence, UI and same-PR Help/diagram/
screenshot updates as applicable, meaningful boundary tests and independent review.
If a slice exceeds a reviewable size, Main splits its contracts before launch and
records exact dependencies. Broader formats, extraction summaries, replacements,
cloud workflows and learned skills require separately scoped follow-ups. See
[ORB-010 coverage and examples](work-items/ORB-010.md). Folder task completion
never triggers Git merge; all changes to Orbit still follow repository PR rules.
