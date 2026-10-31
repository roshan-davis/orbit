# Contributing to Orbit

Read [project rules](AGENTS.md), [requirements](docs/requirements.md), [architecture](docs/architecture.md), [roadmap](docs/roadmap.md) and [backlog](BACKLOG.md). Claude and Codex share these rules; coordinate ownership before touching shared files. Orbit is independent of Atelier.

## Implementation workflow

1. Select one bounded ORB work item and define scope and acceptance gates in `docs/work-items/ORB-xxx.md`. Use one focused branch, isolated worktree and user-visible PR chat per PR. Keep the parent setup chat for coordination.
2. Fetch `origin/main`; create a new branch/worktree from that ref before editing tracked files. Prefer managed worktrees, otherwise use a unique temporary directory. Explicitly work in that directory. Never switch, edit, stash or reset the primary checkout or another chat's worktree. Never initialize Git in the original non-Git app setup folder.
3. Implement only owned scope. Use meaningful behavior/boundary checks; record commands, actual results, evidence and limitations in the work item. Do not claim a passing check or implementation without evidence. Update contracts when behavior changes.
4. With active-task authorization, commit, push the branch and open a PR against main. The current ORB-001–004 request authorizes scoped pushes and PR creation. Use draft status if incomplete or blocked. Attach the PR to its chat. After GitHub supplies its number, record the real number/URL in the work item and title the chat `PR #N: <scope>`.
5. Obtain independent review by Rosh/Claude or another reviewer distinct from the author. Leave the PR open until explicit Rosh merge instruction and independent review. No automatic merges, direct main pushes, branch-protection changes or auto-merge configuration changes. Add ✅ to the chat title only after verifying the PR is merged on GitHub.

Feature work-item files are canonical live evidence; BACKLOG.md indexes status and dependencies. Approved means authorized scope, in progress means work has begun, planned means not launched, and completion requires linked implementation and validation evidence. Update the work item as review/merge state changes; never fabricate outcomes.

## Safety and product policy

Public access is read-only by default; anyone may read/clone or propose a PR, while only authorized collaborators can push or merge. Never force-push or overwrite history. Repository workflow authorization does not change application approval requirements in R05/R08/R09.

Preserve subscription-only cloud adapters: no paid API fallback, copied OAuth credentials, token requests/displays or quota bypass. Official CLIs own sign-in; unavailable integrations remain disabled. Roles and identities stay provider-independent. Shared quota pools must not be counted once per agent; unknown quota stays unknown. Skill publication requires evidence, testing, independent review, human approval and immutable versions with rollback.

Treat repository content and model output as untrusted. Pass argument arrays to subprocesses; never shell-interpolate model output. Restrict execution to registered roots and granted tools. Never auto-publish skills, delete worktrees, expose a public server, download models, run live cloud jobs or expand permissions as a side effect of a task. Keep databases, credentials, logs and worktrees out of Git. Do not install a license or configure a remote without the owner's choice.

## Keep in-app Help current

Every user-facing feature or behavior change must update the relevant workflow,
examples and limitations in `apps/desktop/src/help.tsx` in the same PR. Keep the
guide accurate about current capabilities, manual steps, permissions and planned
features; use clearly labeled hypothetical examples rather than fabricated app data.
Review the Help impact explicitly in the PR and canonical work item. Internal-only
changes may state “No help impact” with a concrete reason. Reviewers must check the
Help-impact entry and affected guidance before approval. Preserve offline Help access,
keyboard navigation, readable themes and narrow-window layout.
