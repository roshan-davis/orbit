"""Task checkout creation. No cleanup, remote operations, or integration actions."""
from dataclasses import dataclass
from pathlib import Path
import re

from .projects import ProjectError, canonical_directory, git, inspect_project


@dataclass(frozen=True)
class TaskWorktree:
    project_root: Path
    base_sha: str
    branch: str
    path: Path


def create_task_worktree(
    project_root: str | Path, *, approved_parent: str | Path,
    task_name: str, branch: str, base_sha: str,
) -> TaskWorktree:
    """Create one uniquely named checkout from a full, existing commit object ID.

    The caller grants the parent directory; this service does not grant access.
    Parents must exist and be canonical, outside every checkout of this repo.
    Names use a deliberately narrow portable alphabet. Collisions fail; callers
    choose a new name explicitly. Failures never trigger removal or rollback.
    """
    project = inspect_project(project_root)
    parent = canonical_directory(approved_parent)
    if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_-]{0,79}', task_name):
        raise ProjectError('Invalid task name')
    if (not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9/_-]{0,119}', branch)
            or any(not part or part.startswith('-') for part in branch.split('/'))):
        raise ProjectError('Invalid task branch')
    git(project.root, 'check-ref-format', '--branch', branch)
    if not re.fullmatch(r'(?:[0-9a-f]{40}|[0-9a-f]{64})', base_sha):
        raise ProjectError('Base must be a full lowercase commit SHA')
    if git(project.root, 'cat-file', '-t', base_sha) != 'commit':
        raise ProjectError('Base must identify a commit, not a tag/tree/blob')
    # NUL records avoid interpreting spaces, newlines or quoting in paths.
    listing = git(project.root, 'worktree', 'list', '--porcelain', '-z')
    roots = [Path(record[len('worktree '):]).resolve()
             for record in listing.split('\0') if record.startswith('worktree ')]
    for forbidden in [*roots, project.common_directory]:
        if parent == forbidden or forbidden in parent.parents:
            raise ProjectError('Worktree parent must be outside project checkouts and Git metadata')
    destination = parent / task_name
    if destination.exists() or destination.is_symlink():
        raise ProjectError('Destination already exists; nothing was overwritten')
    existing = git(project.root, 'for-each-ref', '--format=%(refname)', 'refs/heads/')
    if 'refs/heads/' + branch in existing.splitlines():
        raise ProjectError('Task branch already exists')
    # Git performs its own branch/path collision checks as well. Do not force or
    # clean up on failure: a timeout may leave a valid checkout or branch.
    git(project.root, 'worktree', 'add', '-b', branch, '--', str(destination), base_sha)
    return TaskWorktree(project.root, base_sha, branch, destination)
