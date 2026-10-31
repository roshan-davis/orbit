# Working on Orbit

Read README.md, CONTRIBUTING.md and the relevant architecture/requirements before changes.

## Git workflow

The owner prefers separate Git worktrees for changes. Create a focused branch and worktree before editing tracked files; keep the primary checkout clean. Run appropriate validation in that worktree, commit there, and integrate only the intended changes. Do not edit another agent's worktree or discard unrelated work.

Public repository: https://github.com/roshan-davis/orbit. Public access is read-only; only authorized collaborators can push or merge. Publishing changes still requires authorization from the active task. Never force-push or overwrite existing history.

## Product constraints

Cloud providers use their supported subscription-authenticated native CLIs with no paid API fallback. Credentials remain outside Git. Keep unavailable integrations disabled, quota uncertainty explicit, shared provider pools deduplicated, and skill publication subject to review and human approval.
