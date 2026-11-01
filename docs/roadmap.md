# Phased implementation

| Phase | Deliverables | Exit gate |
| --- | --- | --- |
| 0 — Foundation (this setup) | Independent Git repository, docs, desktop shell, SQLite agent API, provider declarations, tests | API tests and UI build pass; native-build limitations recorded |
| 1 — Dependable connected development mission | Project registry, agent editing, task state machine, Git worktree manager, Ollama adapter, logs/cancellation | Connected desktop development request runs with actual checks/review evidence, revision and restart/cancel boundaries; owned startup/connection is a near-term companion gate; no primary-checkout mutation |
| 2 — Subscription CLI support | Independently validate Claude Code, Codex CLI, Gemini CLI sign-in/machine output, capability detection and process handling | Contract tests with fixtures, opt-in real smoke tests per installed CLI; missing subscription auth fails closed, no API fallback |
| 3 — Team orchestration | Bounded automatic development follow-through, dependency queue, actual independent review, human integration decisions, restart recovery | Two independent agents implement/review; rejection and conflicts block merge; duplicate/restart tests pass |
| 4 — Energy and scheduling | Shared account pools, windows, stale/unknown observations, reserves, local compute | Shared agents never double-count pools; short/long limits and unknown states tested |
| 5 — Skill evolution | Periodic observer, architect proposals, evaluations, independent review, approval and registry | Unapproved version cannot activate; regression rollback demonstrated; skill/knowledge/automation classification |
| 6 — Desktop distribution | Managed Python sidecar, secure token bootstrap, migration backups, packaging/signing | Clean-machine install, lifecycle, upgrade/restore and accessibility validation |
| 7 — Private multi-device access | Device pairing, encrypted private transport, scoped permissions, remote dashboard | Unauthorized/revoked devices denied; remote approval audit and reconnect tested |
| 8 — Design integrations | Google Stitch / Claude design discovery and supported connectors | Verified access and cost policy, artifact round-trip, accessibility and design-to-code review |

## Development-first delivery sequence (planned)

Rosh's clarified priority supersedes the earlier folder-inventory-first proposal.
The phase table is a set of capabilities/release gates, not a requirement to finish
all orchestration before any useful folder flow. Near-term startup/connection work
from phase 6 moves alongside the complete development mission. Only ORB-010
planning/guidance is launched here; the slices below have no reserved ORB IDs or
implementation authorization. Main checks live PR/work-item state, assigns owners
and serializes shared docs before launching each bounded PR.

| Priority / slice | Bounded implementation PR | Dependencies | Acceptance gate |
| --- | --- | --- | --- |
| 1 / D1 | Complete connected desktop development mission | Existing ORB-005–009 preview | Run a real bounded development request through create/assign/grant/run, inspect retained diff, relevant manual checks, actual independent manual review, revision if needed and completion. Preserve primary checkout; disclose manual steps and native lifecycle/restart limits. Do not claim autonomous coding or merge. |
| 1 / D2 | Owned engine startup/connection | Existing manual engine contract; coordinate with D1 | Owned child health/lifecycle, secure ephemeral session handoff, stable data location, reconnect/startup failure and restart evidence; no orphaned/duplicate engine or token logs. Full distribution/signing remains phase 6. |
| 2 / D3 | One supported subscription CLI adapter | Provider contracts; D1 evidence | Verify official subscription auth/capabilities and bounded process/cancel fixtures, opt-in installed-CLI smoke; unavailable access blocks actionably. No API fallback or copied credentials. Repeat separately per provider. |
| 3 / D4 | Minimal versioned development actions and direct workflow | Existing isolation/run contracts; D3 where CLI-dependent | Pin trusted repo-inspect/worktree/approved-check/diff handlers with typed schemas, effects/grants, timeout/cancel/recovery and run evidence; direct UI invocation works. First acceptance proves a useful development change/checks/diff, not folder inventory. PR preparation is a separately granted network effect. |
| 2 / D5 | Role/task model selection, automatic bounded task progression and actual reviewer execution | D4; supported agents/adapters from D3 or local capabilities | Validate configured default/allowed model bindings by task/role and evidence; demonstrate older/smaller eligible selection, unsupported-setting rejection and unavailable-model blocking without silent substitution. Snapshot exposed version/settings/policy/reason and alias limits. Claim scoped dependent steps, implement/check/fix, launch reviewer distinct from author, address findings/recheck and prepare PR evidence without routine continue prompts. Rejection loops to revision; missing access/cost/scope decisions become actionable blockers. Restart avoids duplicate effects; no hidden provider changes. Split binding policy/snapshot, progression, reviewer and PR preparation into separate bounded PRs before launch. |
| 3 / D6 | Local intent/entity selection over development templates | D4; installed model discovery | Known workflow/version and typed inputs, ambiguous required inputs clarify, unsupported requests block; direct fallback works offline. Validate independently of model; no arbitrary shell/native-tool assumption. Can proceed alongside D5. |
| 2 / D7 | Human integration decision and verified status | D5 review/PR evidence | Request explicit Rosh merge approval tied to reviewed revision/checks; changed head/conflict blocks integration. Only when authorized, verify GitHub integration and update evidence/status. Task completion is distinct from merge; no unattended merge. |
| 4 / E1 | Separate folder project/workspace registration and staging contracts | D4 shared-core development acceptance; project/workspace migration | Preserve Git behavior and per-project context/files/history/grants; non-Git folder needs no `.git`. Define no-clobber separate-output preview, source/destination checks and crash/recovery manifest protocol. Inventory may be a technical fixture only. |
| 4 / E2 | One supported photo resize/JPEG export workflow | E1; registered image parser/action; D4 templates | Explicit selected sources/dimensions/quality/destination; preserve originals, preview outputs/collisions, required approval, verify dimensions/format/integrity and visual evidence as applicable. Report succeeded/failed/skipped and actual effects; cancel/restart/partial failures reconcile. Direct invocation; risk-based review rather than universal second agent. No generic image support. |
| 5 | Broader scheduling/capacity and learned skills, separately bounded | Mature shared core and evidence | Preserve phase 4 quota honesty and phase 5 evaluation/review/human publication gates; learning never expands permissions. |

D4 supplies the foundation needed to reduce supervision in D5; priority numbers
express product outcomes, while dependencies express technical order. E1/E2 may
ship after demonstrated shared-core development value while remaining D5–D7
orchestration increments continue; they do not wait for all future orchestration,
scheduling or skills. In-place photo edits, replacements/deletes, broader parsers,
contact sheets and folder recovery actions each need separately scoped follow-ups.

Every slice owns contracts/persistence/UI and same-PR Help, affected diagrams and
tutorial screenshots, meaningful boundary checks and independent PR review. Keep
scope reviewable by splitting before launch. Preserve focused UI, keyboard access,
themes/smaller windows and truthful empty/error/blocked states. See
[ORB-010 coverage and examples](work-items/ORB-010.md). Repository changes to Orbit
still require isolated PRs, independent review and explicit Rosh merge authorization.
