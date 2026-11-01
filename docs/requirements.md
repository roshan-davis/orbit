# Product requirements

## Vision and provenance
Orbit is local-first agent orchestration for developing apps with minimal
hand-holding: **Many minds. One mission.** Atelier is an example managed development
project, never Orbit's repository or a dependency. Ordinary-folder projects, such
as photo processing, are a secondary extension using the same core.

Rosh clarified this priority on October 31, 2026 after the folder/action proposal:
dependable development missions and reduced supervision come first; shared actions
must first prove development value. Folder inventory is an optional technical
fixture, not the primary milestone. [ORB-010](work-items/ORB-010.md) records the
clarification and superseded proposal without claiming implementation.

Source: user setup brief and the available October 31, 2026 conversation, “Multi Agent Orchestration” (`6ae602fb-f7dc-83e8-b28b-28f8d641309a`). The reader exposed five recent discussion turns, including roles, skill evolution, energy, design integrations and setup. Earlier discussion was unavailable through that reader; the explicit setup brief supplies the remaining stack decisions. Illustrative agent names and dashboard values are not real configuration or telemetry.

## Required behavior
| ID | Requirement | Acceptance criterion |
| --- | --- | --- |
| R01 | Local-first Tauri 2, React/TypeScript desktop; FastAPI engine; SQLite | Core state works without a cloud account; database survives restart. |
| R02 | Independent project and workspace | Project owns goal, instructions, configured team, missions/tasks, decisions/history and acceptance. Begin with one primary workspace defining kind, canonical roots, scope and isolation. Git development and ordinary-folder work are separate projects; no implicit cross-project context/files/history/grants. Folder work never requires `git init`, branches or commits. |
| R03 | Persistent agent identity | Store name, instructions, role, seniority, expertise, skills, tool permissions and model binding; switching providers preserves identity/history; reuse across projects grants only assignment-scoped context/access, never implicit sharing. |
| R04 | Flexible assignments | Assemble mission teams dynamically by capability, role, availability and permissions; multiple agents may share a role/provider. Seniority is assigned authority, not a model quality guarantee. Select among explicitly supported model families, versions and capability tiers for the role/task under configured policy; newer/larger is not automatically better. |
| R05 | Tasks and peer review | Tasks have dependencies, acceptance criteria, artifacts and audit history; critical changes require a reviewer distinct from the author. Development requires actual independent review distinct from the author, with rejection returning to revision. Risk/artifact policy governs folder review and approvals; routine conversions need not require a second agent. Policy governs action approvals and artifact sign-off; Git merge separately requires explicit approval in Git workspaces. Folder completion never implies Git merge. |
| R06 | Cloud CLI adapters | Claude Code, Codex CLI and Gemini CLI use each CLI's supported subscription/account authentication. Missing entitlement or unsupported mode blocks execution; never fall back to paid APIs. |
| R07 | Local model adapter | Support Ollama with installed Gemma/Qwen models and other installed local/open models through explicitly supported adapters to propose known workflow IDs and typed entities/parameters. Detect capabilities; native tools are not assumed. Missing/ambiguous inputs require clarification, unsupported intents stay blocked, and direct invocation works without model routing. No automatic downloads. |
| R08 | Git and folder isolation | For Git implementation, use dedicated branches/worktrees, preserve user changes, show diffs/conflicts and review before explicitly approved merge; obtain approval before destructive cleanup. For folder effects, stage, preview and validate scope/collisions/source versions before approved apply; retain recovery evidence and explicit partial outcomes (R19). |
| R09 | Skill evolution | Observer → Architect → Tester → Reviewer → human approval → immutable versioned publication with rollback; retain evidence, tests, permissions and history. Predefined deterministic actions/workflows (R16–R17) are usable independently; learning or publication never grants execution permissions. |
| R10 | Honest energy | Agents reference shared account/provider quota pools and all active windows; distinguish measured/estimated/unknown, reset times, freshness and confidence. Never duplicate a pool per agent. |
| R11 | Team capacity | Aggregate only independent pools with explicitly comparable capacity weights; otherwise show pools individually. Unknown values remain unknown. Show local compute separately. |
| R12 | Quota-aware scheduling | Respect user reserves, short/long windows, depleted pools, concurrency and uncertain telemetry; pause or offer an approved alternative without silently changing providers. |
| R13 | Private remote access later | Phone and other desktop monitor/control via authenticated encrypted private access, device revocation and audited approvals; no public listener by default. |
| R14 | Future design workflows | Plan Google Stitch and Claude design connectors: concept import, critique, accessibility review, implementation and shared design memory. Verify supported access and costs before implementation. |
| R15 | Auditable memory | Separate workspace knowledge from portable agent history; inspect, export and delete local memory; redact secrets, scope access and record inspectable action results without routine sensitive document bodies. |
| R16 | Registered deterministic actions | Stable action ID/version, typed input/output schemas, registered handler, declared effects/read/write/network permissions, limits, previews and timeout/cancel/retry/recovery contracts. Executor rejects unknown versions, invalid arguments and undeclared effects; no model-generated shell execution. |
| R17 | Versioned workflow templates | Pin action versions, step dependencies, typed input/output mappings, acceptance checks and approval boundaries; direct invocation needs no model. Persist exact resolved versions/inputs; templates cannot widen grants. |
| R18 | Independent execution enforcement | Engine validates model proposals and direct calls identically against schema, workspace kind, scope and policy. Reject traversal/symlink escapes, secret access and unapproved network use; imported content cannot authorize actions. Record approvals against exact scope/effects and invalidate on material changes. |
| R19 | Folder staging and recovery | Preview creates/moves/replacements, detect collisions and changed sources/destinations before apply, retain manifest/originals where applicable and recovery instructions. No silent overwrite, atomicity or universal reversibility claim. Cancellation, partial failure and restart reconcile actual effects before retry. |
| R20 | Auditable action runs | Persist run/step IDs, pinned versions, redacted validated inputs, grant/approval evidence, progress, outputs, acceptance results and explicit failures. Completion derives from inspected artifacts/checks, not model claims. |
| R21 | Routine development follow-through | Within authorized scope, Orbit reads request/project rules, defines acceptance and bounded plan/dependencies, assigns capable configured agents, implements in isolated worktrees, runs relevant tests/builds and fixes failures, obtains actual independent review and resolves findings, prepares PR/evidence, requests explicit human merge authorization, then verifies authorized integration and updates status. Users need not repeatedly request continue/test/fix/status. |
| R22 | Human decision boundaries | Ask for material ambiguity, direction/scope/cost decisions, unavailable access/provider, permission expansion or required approval. Routine follow-through proceeds within grants. No hidden provider change, paid fallback, unattended merge or uncontrolled scope expansion; safe restart reconciles effects before repeating work. |

## Role- and task-based model selection (planned)

An agent identity is independent of its provider/model binding. Configure a default
binding and allowed alternatives, including supported older versions, smaller/local
models or more capable tiers. Choose using role, expertise, task complexity/risk,
demonstrated capability, supported features/context limits, availability, subscription
entitlement/quota or local compute, permissions and user cost preferences. Marketing
names, recency and assigned seniority are not capability evidence. An architect may
need stronger planning capability, an implementer coding capability, a distinct
reviewer review capability and routine classification a smaller local model; these
are examples, not fixed provider roles or guarantees.

Record the selected provider, exact exposed model identifier/version, supported
settings, selection rationale and capability/readiness evidence in each assignment
snapshot. Pin an immutable revision/digest where supported; if a provider exposes
only a mutable alias, record that limitation rather than claiming exact weights are
pinned. Later profile/default changes never alter an existing assignment. Validate
capabilities and readiness before running; unsupported settings stay unavailable.

Selection and any alternative must be explicit and auditable. An already-approved
selection policy may choose among its named alternatives for a new assignment,
within the same scope/cost/permission grant; it cannot silently replace the model
of an existing assignment or switch providers after failure. If no eligible binding
is ready, block with a useful explanation and request any required human decision.
Provider/permission/cost expansion needs approval; no hidden paid API fallback,
model download or entitlement/quota bypass. Current preview saves one provider/model
binding and snapshots it; policy selection, richer version/settings records and
automatic role/task routing remain planned.

## Development orchestration and shared actions (planned)

The first outcome is a tested, independently reviewed development change ready for
human integration decision, with actionable blockers instead of repeated supervision.
Dedicated branch/worktree execution records base revision/configuration, actual
diffs and relevant checks. Review findings create revisions; conflicts block
integration. Worktree isolation never substitutes for permission/process enforcement.
Mission completion and merge are separate facts. The human authorizes merge;
Orbit verifies integration only when authorized and records actual status.

Shared trusted actions include repository inspection, worktree creation, approved
tests/builds, diff collection and PR preparation. Versioned workflows pin these
actions and map inputs/dependencies. Installed local/open models can select known
workflows and extract intent/entities/parameters; the engine validates schemas,
grants and policy, clarifies consequential missing required inputs, previews effects
and obtains required approval. The model proposes; the executor enforces. Direct
UI invocation follows the same boundary without routing. Never execute arbitrary
model-produced shell text. Fixed actions/workflows are independent of learned
skills under R09; learning cannot grant permissions.

A later separate photo project may resize selected supported photos for a website,
resolve source/dimensions/quality/destination, preserve originals and export JPEGs
separately. Preview outputs/collisions, execute approved actions, verify dimensions,
format/integrity and visual evidence where applicable, then report succeeded,
failed and skipped files with effects recorded. In-place edits, replacements and
deletes need explicit approval/recovery contracts. Do not imply image/binary support
beyond implemented parsers/actions. Useful folder delivery need not wait for the
entire future orchestration/scheduling roadmap, but does not displace development.

Current preview: ORB-007 is a narrow Git-worktree UTF-8 replacement protocol. It is
not full autonomous coding, supported cloud CLI orchestration, actual reviewer
execution, generic folder/image processing or a validated full desktop lifecycle.
Tests, review and integration are currently manual; engine startup/session entry
are manual. This PR changes guidance/plans, not those capabilities.

## Skill quality
Observer starts with periodic analysis of completed tasks, not continuous expensive monitoring. Require repeated-use evidence, clear triggers, examples, reproducible tests and baseline comparisons. Classify each candidate as reusable skill, knowledge, or deterministic automation. Reviewer checks quality, permissions, portability and usefulness. Track published skill success, regressions, overhead, usage and provider compatibility. Keep immutable versions, an active-version pointer and a disable/rollback path; never uncontrolled self-modification.

## UX and operational quality

Follow the approved lavender/neutral visual direction with focused decision steps,
progressive disclosure and evidence-based statuses. File context limits are UTF-8
bytes. Recorded review is a human-session assertion using a distinct configured
identity; mission completion never merges or pushes Git.

Use the project [design system and component library](design-system.md): semantic theme tokens, consistent controls and status treatments, clear navigation, focused list/detail workspaces and progressive disclosure. Support dark/light themes and smaller windows. Use workspace-kind-aware language: ordinary folders show files, previews, artifacts
and completion, while branch/worktree/merge controls appear only for Git work.
Offer an action/workflow library and “What would you like to do?”, interpreted
inputs, targeted clarification, progress and recovery next steps. Every delivered
user-facing slice must update `apps/desktop/src/help.tsx`, affected diagrams and
tutorial screenshots in the same PR under AGENTS.md; this planning change adds
no live controls. Preserve offline Help, keyboard access, narrow layout and themes.

Put the user’s current mission and next action ahead of setup; avoid presenting every form and evidence section as one long stacked page.
Show missions, team assignments, diffs, approvals, provider readiness, agent energy references and independent pool dashboards. Provide accessible labels, keyboard interaction and readable states. Unknown quota must never look full or depleted. Surface blocked authentication, crashes, cancellation and stale observations. Store locally by default; no telemetry upload. Never persist tokens in prompts/logs. Support restart recovery with no duplicate task execution. Initial target is local macOS development; other desktop packaging follows validation.

## Foundation boundary
The current preview includes the shell, token-protected API/SQLite state, profiles, Git project/task registration, bounded local runs and manual review/completion UI (ORB-005–009). Full development follow-through, shared action routing, generic folders/photos, remote control, memory mining and external design connectors remain planned. Canonical work items record validation limits; declarations alone do not prove runtime readiness.
