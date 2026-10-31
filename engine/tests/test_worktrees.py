from pathlib import Path
import subprocess

import pytest

from orbit_engine.projects import ProjectError, inspect_project
from orbit_engine.worktrees import create_task_worktree


def run(root, *args):
    return subprocess.check_output(['git', '-C', str(root), *args], text=True).strip()


@pytest.fixture
def repo(tmp_path):
    root = tmp_path / 'project ; $(touch injected) space'
    root.mkdir()
    run(root, 'init', '-b', 'main')
    run(root, 'config', 'user.email', 'test@example.invalid')
    run(root, 'config', 'user.name', 'Test')
    (root / 'file').write_text('base')
    run(root, 'add', '.')
    run(root, 'commit', '-m', 'base')
    return root


def create(repo, tmp_path, **overrides):
    args = dict(approved_parent=tmp_path, task_name='task-1', branch='task/one',
                base_sha=run(repo, 'rev-parse', 'HEAD'))
    args.update(overrides)
    return create_task_worktree(repo, **args)


def test_isolation_and_linked_inspection(repo, tmp_path):
    (repo / 'file').write_text('user unstaged')
    (repo / 'new file\n;').write_text('untracked')
    (repo / 'staged').write_text('staged user edit')
    run(repo, 'add', 'staged')
    before = inspect_project(repo)
    result = create(repo, tmp_path)
    assert (result.path / 'file').read_text() == 'base'
    (result.path / 'file').write_text('task edit')
    assert inspect_project(repo) == before
    assert (repo / 'file').read_text() == 'user unstaged'
    linked = inspect_project(result.path)
    assert linked.common_directory == before.common_directory
    assert linked.git_directory != before.git_directory
    assert linked.branch == result.branch
    assert linked.head_sha == result.base_sha
    assert not (tmp_path / 'injected').exists()
    run(result.path, 'checkout', '--detach')
    assert inspect_project(result.path).branch is None


@pytest.mark.parametrize('name', ['../escape', '-bad', 'a/b', 'x;touch x', 'x y', '', 'x\n'])
def test_bad_task_names(repo, tmp_path, name):
    with pytest.raises(ProjectError):
        create(repo, tmp_path, task_name=name)


@pytest.mark.parametrize('branch', ['-bad', 'main', 'x..y', 'x.lock', 'x//y', 'x/-y', 'x;ls', 'x y', 'HEAD'])
def test_bad_or_existing_branches(repo, tmp_path, branch):
    with pytest.raises(ProjectError):
        create(repo, tmp_path, branch=branch)


@pytest.mark.parametrize('ref', ['HEAD', '--help', 'main^{commit}', '0'*40, 'abc', 'a\n'])
def test_invalid_base(repo, tmp_path, ref):
    with pytest.raises(ProjectError):
        create(repo, tmp_path, base_sha=ref)


def test_blob_base(repo, tmp_path):
    with pytest.raises(ProjectError):
        create(repo, tmp_path, base_sha=run(repo, 'rev-parse', 'HEAD:file'))


def test_root_and_parent_boundaries(repo, tmp_path):
    sub = repo / 'sub'
    sub.mkdir()
    alias = tmp_path / 'alias'
    alias.symlink_to(repo, target_is_directory=True)
    for root in [sub, alias, tmp_path, tmp_path / 'absent', Path('relative')]:
        with pytest.raises(ProjectError):
            inspect_project(root)
    for parent in [repo, sub, alias, repo / '.git', tmp_path / 'absent']:
        with pytest.raises(ProjectError):
            create(repo, tmp_path, approved_parent=parent)
    linked = create(repo, tmp_path)
    with pytest.raises(ProjectError):
        create(repo, tmp_path, task_name='two', branch='task/two', approved_parent=linked.path)


def test_destination_collision_preserves_data(repo, tmp_path):
    target = tmp_path / 'task-1'
    target.mkdir()
    (target / 'precious').write_text('keep')
    with pytest.raises(ProjectError):
        create(repo, tmp_path)
    assert (target / 'precious').read_text() == 'keep'
    (target / 'precious').unlink()
    with pytest.raises(ProjectError):
        create(repo, tmp_path)  # Even an empty existing directory is refused.
    target.rmdir()
    target.symlink_to(tmp_path / 'missing')
    with pytest.raises(ProjectError):
        create(repo, tmp_path)
    assert target.is_symlink()


def test_branch_collision_and_git_failure(repo, tmp_path, monkeypatch):
    create(repo, tmp_path)
    with pytest.raises(ProjectError):
        create(repo, tmp_path, task_name='another')
    import orbit_engine.projects as projects
    base = run(repo, 'rev-parse', 'HEAD')
    real_run = projects.subprocess.run
    def fail(args, **kwargs):
        if 'add' in args:
            # Simulate a timeout after Git left partial branch/path state.
            (tmp_path / 'other').mkdir()
            (tmp_path / 'other' / 'user-data').write_text('preserve')
            raise subprocess.TimeoutExpired('git', 30)
        return real_run(args, **kwargs)
    monkeypatch.setattr(projects.subprocess, 'run', fail)
    with pytest.raises(ProjectError, match='inspect repository state'):
        create_task_worktree(repo, approved_parent=tmp_path, task_name='other',
                             branch='task/other', base_sha=base)
    assert (tmp_path / 'other' / 'user-data').read_text() == 'preserve'
    assert (tmp_path / 'task-1' / 'file').read_text() == 'base'


def test_unborn(repo, tmp_path):
    empty = tmp_path / 'empty'
    empty.mkdir()
    run(empty, 'init', '-b', 'main')
    assert inspect_project(empty).head_sha is None


def test_git_environment_is_not_inherited(repo, tmp_path, monkeypatch):
    monkeypatch.setenv('GIT_DIR', str(tmp_path / 'not-a-repo'))
    assert inspect_project(repo).root == repo


def test_bare_repository_rejected(tmp_path):
    bare = tmp_path / 'bare'
    subprocess.check_call(['git', 'init', '--bare', str(bare)])
    with pytest.raises(ProjectError):
        inspect_project(bare)


def test_missing_git(repo, monkeypatch):
    import orbit_engine.projects as projects
    def missing(*args, **kwargs):
        raise FileNotFoundError('git')
    monkeypatch.setattr(projects.subprocess, 'run', missing)
    with pytest.raises(ProjectError, match='could not complete'):
        inspect_project(repo)


def test_hooks_disabled(repo, tmp_path):
    hook = repo / '.git' / 'hooks' / 'post-checkout'
    marker = tmp_path / 'hook-ran'
    hook.write_text('#!/bin/sh\ntouch "' + str(marker) + '"\n')
    hook.chmod(0o755)
    create(repo, tmp_path)
    assert not marker.exists()


def test_partial_clone_never_fetches(repo, tmp_path):
    run(repo, 'config', 'uploadpack.allowFilter', 'true')
    clone = tmp_path / 'partial'
    subprocess.check_call(['git', 'clone', '--filter=blob:none', '--no-checkout',
                           repo.as_uri(), str(clone)])
    missing_before = run(clone, 'rev-list', '--objects', '--all', '--missing=print')
    assert any(line.startswith('?') for line in missing_before.splitlines())
    base = run(clone, 'rev-parse', 'HEAD')
    with pytest.raises(ProjectError, match='Partial/promisor'):
        create_task_worktree(clone, approved_parent=tmp_path, task_name='partial-task',
                             branch='task/partial', base_sha=base)
    assert run(clone, 'rev-list', '--objects', '--all', '--missing=print') == missing_before
    assert not (tmp_path / 'partial-task').exists()
    assert 'task/partial' not in run(clone, 'branch', '--list')


@pytest.mark.parametrize('key', ['extensions.partialClone', 'remote.origin.promisor'])
def test_promisor_config_rejected(repo, key):
    run(repo, 'config', key, 'true')
    with pytest.raises(ProjectError, match='Partial/promisor'):
        inspect_project(repo)
