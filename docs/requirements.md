# Product requirements

## Vision and provenance
Orbit is a project-agnostic, local-first desktop application: **Many minds. One mission.** Atelier is one potential managed project, not a dependency or parent repository.

Source: user setup brief and the available October 31, 2026 conversation, “Multi Agent Orchestration” (`6ae602fb-f7dc-83e8-b28b-28f8d641309a`). The reader exposed five recent discussion turns, including roles, skill evolution, energy, design integrations and setup. Earlier discussion was unavailable through that reader; the explicit setup brief supplies the remaining stack decisions. Illustrative agent names and dashboard values are not real configuration or telemetry.

## Required behavior
| ID | Requirement | Acceptance criterion |
| --- | --- | --- |
| R01 | Local-first Tauri 2, React/TypeScript desktop; FastAPI engine; SQLite | Core state works without a cloud account; database survives restart. |
| R02 | Any registered project | Select independent repository roots; no Atelier paths or domain logic. |
| R03 | Persistent agent identity | Store name, instructions, role, seniority, expertise, skills, tool permissions and model binding; switching providers preserves identity/history. |
| R04 | Flexible assignments | Assemble mission teams dynamically by capability, role, availability and permissions; multiple agents may share a role/provider. Seniority is assigned authority, not a model quality guarantee. |
| R05 | Tasks and peer review | Tasks have dependencies, acceptance criteria, artifacts and audit history; critical changes require a reviewer distinct from the author and explicit merge approval. |
| R06 | Cloud CLI adapters | Claude Code, Codex CLI and Gemini CLI use each CLI's supported subscription/account authentication. Missing entitlement or unsupported mode blocks execution; never fall back to paid APIs. |
| R07 | Local model adapter | Ollama with installed Gemma/Qwen models; detect model capabilities rather than assuming equivalent tools. No automatic model downloads. |
| R08 | Git isolation | Dedicated branch/worktree per implementation; preserve user changes, show diffs and conflicts, review before merge; approval before destructive cleanup. |
| R09 | Skill evolution | Observer → Architect → Tester → Reviewer → human approval → versioned publication; retain evidence, tests, permissions, history and rollback. |
| R10 | Honest energy | Agents reference shared account/provider quota pools and all active windows; distinguish measured/estimated/unknown, reset times, freshness and confidence. Never duplicate a pool per agent. |
| R11 | Team capacity | Aggregate only independent pools with explicitly comparable capacity weights; otherwise show pools individually. Unknown values remain unknown. Show local compute separately. |
| R12 | Quota-aware scheduling | Respect user reserves, short/long windows, depleted pools, concurrency and uncertain telemetry; pause or offer an approved alternative without silently changing providers. |
| R13 | Private remote access later | Phone and other desktop monitor/control via authenticated encrypted private access, device revocation and audited approvals; no public listener by default. |
| R14 | Future design workflows | Plan Google Stitch and Claude design connectors: concept import, critique, accessibility review, implementation and shared design memory. Verify supported access and costs before implementation. |
| R15 | Auditable memory | Separate project knowledge from portable agent history; inspect, export and delete local memory; redact secrets and scope project access. |

## Skill quality
Observer starts with periodic analysis of completed tasks, not continuous expensive monitoring. Require repeated-use evidence, clear triggers, examples, reproducible tests and baseline comparisons. Classify each candidate as reusable skill, knowledge, or deterministic automation. Reviewer checks quality, permissions, portability and usefulness. Track published skill success, regressions, overhead, usage and provider compatibility. Keep immutable versions, an active-version pointer and a disable/rollback path; never uncontrolled self-modification.

## UX and operational quality
Show missions, team assignments, diffs, approvals, provider readiness, agent energy references and independent pool dashboards. Provide accessible labels, keyboard interaction and readable states. Unknown quota must never look full or depleted. Surface blocked authentication, crashes, cancellation and stale observations. Store locally by default; no telemetry upload. Never persist tokens in prompts/logs. Support restart recovery with no duplicate task execution. Initial target is local macOS development; other desktop packaging follows validation.

## Foundation boundary
This setup implements the shell, token-protected profile API, SQLite persistence and provider declarations. The rest is phased work. Remote control, automatic routing, memory mining, and external design connectors are explicitly later scope.
