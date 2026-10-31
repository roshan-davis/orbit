"""Read-only inspection of explicitly selected, canonical Git checkout roots."""
from dataclasses import dataclass
import os
from pathlib import Path
import subprocess


class ProjectError(ValueError):
    """Invalid project input or a failed Git operation."""


def canonical_directory(value: str | Path) -> Path:
    path = Path(value)
    try:
        resolved = path.resolve(strict=True)
    except (OSError, RuntimeError) as exc:
        raise ProjectError("Directory must exist") from exc
    if not path.is_absolute() or path != resolved or not resolved.is_dir():
        raise ProjectError("Use an absolute canonical directory, without symlinks or traversal")
    return resolved


def git(root: Path, *args: str, missing_ok: bool = False) -> str:
    # Do not inherit Git routing/config injection from the hosting process.
    env = {k: v for k, v in os.environ.items() if not k.startswith('GIT_')}
    env.update(GIT_TERMINAL_PROMPT='0', GIT_OPTIONAL_LOCKS='0')
    try:
        result = subprocess.run(
            ['git', '-c', 'core.hooksPath=/dev/null', '-c', 'core.fsmonitor=false',
             '-C', str(root), *args],
            env=env, capture_output=True, text=True, errors='surrogateescape',
            timeout=30, check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise ProjectError("Git operation could not complete; inspect repository state") from exc
    if missing_ok and result.returncode == 1:
        return ""
    if result.returncode:
        raise ProjectError(f"Git operation failed ({result.returncode}); inspect repository state")
    return result.stdout.rstrip('\n')


@dataclass(frozen=True)
class ProjectInspection:
    root: Path
    git_directory: Path
    common_directory: Path
    head_sha: str | None
    branch: str | None
    status_porcelain: str


def inspect_project(root: str | Path) -> ProjectInspection:
    """Accept primary or linked checkout roots; reject bare repos and subdirectories.

    Symlink aliases are rejected: callers must first present the canonical root.
    Status is porcelain v1 with NUL separators (including unusual filenames).
    """
    path = canonical_directory(root)
    if git(path, 'rev-parse', '--is-inside-work-tree') != 'true':
        raise ProjectError('A non-bare Git checkout is required')
    if Path(git(path, 'rev-parse', '--show-toplevel')).resolve() != path:
        raise ProjectError('Select the checkout top-level directory')
    git_dir = Path(git(path, 'rev-parse', '--absolute-git-dir')).resolve()
    common_dir = Path(git(path, 'rev-parse', '--path-format=absolute', '--git-common-dir')).resolve()
    head = git(path, 'rev-parse', '--verify', '--quiet', '--end-of-options',
               'HEAD^{commit}', missing_ok=True) or None
    branch = git(path, 'symbolic-ref', '--quiet', '--short', 'HEAD', missing_ok=True) or None
    return ProjectInspection(path, git_dir, common_dir, head, branch,
                             git(path, 'status', '--porcelain=v1', '-z', '--untracked-files=all'))
