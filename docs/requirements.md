# Product requirements

## Vision and provenance
Orbit is a project-agnostic, local-first desktop application: **Many minds. One mission.** Atelier is one potential managed project, not a dependency or parent repository.

Source: user setup brief and the available October 31, 2026 conversation, “Multi Agent Orchestration” (`6ae602fb-f7dc-83e8-b28b-28f8d641309a`). The reader exposed five recent discussion turns, including roles, skill evolution, energy, design integrations and setup. Earlier discussion was unavailable through that reader; the explicit setup brief supplies the remaining stack decisions. Illustrative agent names and dashboard values are not real configuration or telemetry.

## Required behavior
| ID | Requirement | Acceptance criterion |
| --- | --- | --- |
| R01 | Local-first Tauri 2, React/TypeScript desktop; FastAPI engine; SQLite | Core state works without a cloud account; database survives restart. |
| R02 | Any registered project | Register typed Git repositories or ordinary folders with canonical allowed input/output roots; folder work never requires `git init`, branches or commits. No project-specific paths or domain logic. |
| R03 | Persistent agent identity | Store name, instructions, role, seniority, expertise, skills, tool permissions and model binding; switching providers preserves identity/history. |
| R04 | Flexible assignments | Assemble mission teams dynamically by capability, role, availability and permissions; multiple agents may share a role/provider. Seniority is assigned authority, not a model quality guarantee. |
| R05 | Tasks and peer review | Tasks have dependencies, acceptance criteria, artifacts and audit history; critical changes require a reviewer distinct from the author. Policy governs action approvals and artifact sign-off; Git merge separately requires explicit approval in Git workspaces. Folder completion never implies Git merge. |
| R06 | Cloud CLI adapters | Claude Code, Codex CLI and Gemini CLI use each CLI's supported subscription/account authentication. Missing entitlement or unsupported mode blocks execution; never fall back to paid APIs. |
| R07 | Local model adapter | Use installed local/open models through supported adapters to propose known workflow IDs and typed entities/parameters. Detect capabilities; native tools are not assumed. Missing/ambiguous inputs require clarification, unsupported intents stay blocked, and direct invocation works without model routing. No automatic downloads. |
| R08 | Git isolation | For Git implementation, use dedicated branches/worktrees, preserve user changes, show diffs/conflicts and review before explicitly approved merge/cleanup. For folder effects, stage, preview and validate scope/collisions/source versions before approved apply; retain recovery evidence and explicit partial outcomes (R19). |
| R09 | Skill evolution | Observer → Architect → Tester → Reviewer → human approval → immutable versioned publication with rollback. Predefined deterministic actions/workflows (R16–R17) are usable independently; learning or publication never grants execution permissions. |
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

## Folder and action alignment (planned)

Rosh's October 31, 2026 direction supports ordinary folder work and explicit predefined
functions, with natural language as an optional route to them. The model proposes;
the executor enforces. [ORB-010](work-items/ORB-010.md) records source intent,
coverage, examples and bounded follow-up gates. No general folder action engine is
implemented by this requirements change. The current ORB-007 runner is a narrow
Git-worktree UTF-8 replacement protocol, not PDF/image/document processing or an
action registry. Supported formats/parsers must be explicitly declared.

Start with bounded metadata inventory and a report available as a run artifact,
without modifying selected source files. Add approved new-artifact creation next;
previewed moves/replacements and recovery come later. Useful deterministic local
work does not depend on cloud subscriptions, scheduling or learned skills.

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
This setup implements the shell, token-protected profile API, SQLite persistence and provider declarations. The rest is phased work. Remote control, automatic routing, memory mining, and external design connectors are explicitly later scope.
