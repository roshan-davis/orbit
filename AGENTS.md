# Working on Orbit

Read README.md, CONTRIBUTING.md, BACKLOG.md, docs/requirements.md, docs/architecture.md and docs/roadmap.md before changing the relevant area. Claude and Codex follow the same rules and coordinate file ownership.

## One work item, one PR

Each PR implements one bounded work item with a stable ORB ID, focused branch, isolated Git worktree and user-visible PR chat. Fetch origin/main and create the branch/worktree from it before editing tracked files. Prefer a managed worktree; if unavailable, use a unique temporary worktree and explicitly use its directory. Never switch, edit, stash or reset the primary checkout or another chat's worktree. Do not initialize Git in the original non-Git app setup folder. Orbit is independent of Atelier; never implement Orbit in Atelier.

Keep the parent setup chat for coordination. Record scope, acceptance criteria, evidence, checks and limitations in docs/work-items/ORB-xxx.md. That file is the canonical live evidence; BACKLOG.md is an index, not proof of implementation. Coordinate shared files and keep each PR within its owned scope.

Push branches and open PRs only when the active task authorizes them. The current ORB-001–004 implementation request authorizes their scoped branch pushes and PR creation, not merging or direct pushes to main. Attach each created PR to its chat. Only after GitHub returns a real PR number, record its URL/number in the work item and rename the chat `PR #N: <scope>`. Never reserve or invent numbers. Use draft status for incomplete or blocked work. Request independent review by Rosh/Claude (or another reviewer distinct from the author). Merge requires explicit Rosh instruction and independent review; never auto-merge. Add ✅ to the chat title only after verifying GitHub reports the PR merged. Do not change branch protection or auto-merge settings as part of implementation.

Public repository: https://github.com/roshan-davis/orbit. Public access is read-only by default: anyone may read/clone or propose a PR; only authorized collaborators can push or merge. Never force-push or overwrite history.

## Product constraints

Repository workflow permission does not alter product approval behavior: docs/requirements.md remains authoritative (especially R05, R08 and R09).

- Preserve independent projects and provider-independent identities, roles and assignments (R02–R04). No provider owns a fixed role.
- Cloud adapters use supported subscription-authenticated native CLIs only (R06). Missing entitlement or unsupported authentication blocks execution; no hidden paid API fallback, credential copying or quota bypass. Credentials stay outside Git and with their official CLI; never request or display tokens.
- Local discovery uses installed models only (R07). No automatic downloads, live cloud execution or public engine listener as a side effect of implementation.
- Shared quota pools are account/provider resources, never duplicated per agent (R10–R12). Preserve measured/estimated/unknown states, freshness and all active windows; aggregate only comparable independent pools. Keep local compute separate.
- Skills require evidence, testing, independent review, human approval and immutable versioned publication with rollback (R09). Never auto-publish or silently expand permissions.
- Keep memory scoped, secrets out of prompts/logs and private remote access gated (R13, R15).

## Completion tracking

When a work item is implemented and its required checks pass, update its
`docs/work-items/ORB-xxx.md` with checked acceptance/validation items and the real
PR link. After GitHub confirms a merge, prefix the PR chat title with `✅` and
mark the matching backlog item complete if a backlog exists. Do this as part of
finishing the work; do not wait for a separate request to add completion marks.
Only mark work complete when the evidence supports it. Completion tracking does
not itself authorize merging; follow the user's merge authorization and required
independent review.

## Keep in-app Help current

Every user-facing feature or behavior change must update the relevant workflow,
examples and limitations in `apps/desktop/src/help.tsx` in the same PR. Refresh
affected diagrams and tutorial screenshots when controls or workflows change. Keep the
guide accurate about current capabilities, manual steps, permissions and planned
features; use clearly labeled hypothetical examples rather than fabricated app data.
Review the Help impact explicitly in the PR and canonical work item. Internal-only
changes may state “No help impact” with a concrete reason. Reviewers must check the
Help-impact entry and affected guidance before approval. Preserve offline Help access,
keyboard navigation, readable themes and narrow-window layout.
