import sqlite3
import subprocess
from concurrent.futures import ThreadPoolExecutor

import pytest
from fastapi.testclient import TestClient
from orbit_engine.app import create_app
from orbit_engine.store import Store
from orbit_engine.models import ProjectInput
from test_api import TOKEN, HEADERS, PROFILE


@pytest.fixture
def repo(tmp_path):
    root = tmp_path.resolve() / 'repo space'
    root.mkdir()
    subprocess.run(['git', 'init', '-b', 'main', str(root)], check=True, capture_output=True)
    (root / 'user.txt').write_text('preserve me')
    return root


def test_registration_restart_selection_and_no_checkout_writes(tmp_path, repo):
    path = tmp_path / 'state.db'
    before = (repo / '.git/index').exists()
    with TestClient(create_app(path, TOKEN)) as client:
        body = {'name': ' Project ', 'root': str(repo)}
        for headers in ({}, {'Authorization': 'Bearer wrong'}):
            for method, route in [('get', '/v1/projects'), ('get', '/v1/projects/missing'), ('post', '/v1/projects')]:
                assert getattr(client, method)(route, headers=headers, **({'json': body} if method == 'post' else {})).status_code == 401
        saved = client.post('/v1/projects', json=body, headers=HEADERS)
        assert saved.status_code == 201
        project = saved.json()
        assert project['name'] == 'Project'
        assert client.post('/v1/projects', json=body, headers=HEADERS).status_code == 409
        assert client.get('/v1/projects/missing', headers=HEADERS).status_code == 404
    with TestClient(create_app(path, TOKEN)) as client:
        assert client.get('/v1/projects', headers=HEADERS).json() == [project]
        assert client.get('/v1/projects/' + project['id'], headers=HEADERS).json() == project
        repo.rename(repo.with_name('moved'))
        assert client.get('/v1/projects/' + project['id'], headers=HEADERS).status_code == 409
        assert client.get('/v1/projects', headers=HEADERS).json() == [project]
    moved = repo.with_name('moved')
    assert (moved / 'user.txt').read_text() == 'preserve me'
    assert (moved / '.git/index').exists() == before


def test_invalid_roots_do_not_persist(tmp_path, repo):
    alias = repo.parent / 'alias'
    alias.symlink_to(repo, target_is_directory=True)
    sub = repo / 'sub'; sub.mkdir()
    with TestClient(create_app(tmp_path / 'state.db', TOKEN)) as client:
        for root in ('relative', str(repo / '..' / repo.name), str(alias), str(sub), str(repo.parent), str(repo / 'missing')):
            assert client.post('/v1/projects', json={'name': 'P', 'root': root}, headers=HEADERS).status_code == 422
        assert client.post('/v1/projects', json={'name': '  ', 'root': str(repo)}, headers=HEADERS).status_code == 422
        assert client.get('/v1/projects', headers=HEADERS).json() == []


def test_v1_migration_retains_profiles_and_is_idempotent(tmp_path):
    import json
    path = tmp_path / 'v1.db'
    with sqlite3.connect(path) as db:
        db.execute('CREATE TABLE agents (id TEXT PRIMARY KEY, profile TEXT NOT NULL)')
        db.execute('INSERT INTO agents VALUES (?, ?)', ('legacy', json.dumps({**PROFILE, 'id': 'legacy'})))
        db.execute('PRAGMA user_version=1')
    for _ in range(2):
        store = Store(path)
        assert store.list_agents()[0].id == 'legacy'
        assert store.list_projects() == []
    with sqlite3.connect(path) as db:
        assert db.execute('PRAGMA user_version').fetchone()[0] == 2


def test_migration_failure_rolls_back_version_and_ddl(tmp_path):
    path = tmp_path / 'broken.db'
    with sqlite3.connect(path) as db:
        db.execute('CREATE TABLE projects (sentinel TEXT)')
    with pytest.raises(sqlite3.OperationalError):
        Store(path)
    with sqlite3.connect(path) as db:
        assert db.execute('PRAGMA user_version').fetchone()[0] == 0
        assert db.execute("SELECT name FROM sqlite_master WHERE name='agents'").fetchall() == []
        assert db.execute('SELECT sentinel FROM projects').fetchall() == []


def test_duplicate_concurrent_registration_is_atomic(tmp_path, repo):
    store = Store(tmp_path / 'state.db')
    def register(_):
        try:
            store.create_project(ProjectInput(name='P', root=str(repo)))
            return 'created'
        except sqlite3.IntegrityError:
            return 'duplicate'
    with ThreadPoolExecutor(max_workers=2) as executor:
        assert sorted(executor.map(register, range(2))) == ['created', 'duplicate']
    assert len(store.list_projects()) == 1


def test_selection_rejects_changed_git_identity(tmp_path, repo):
    with TestClient(create_app(tmp_path / 'state.db', TOKEN)) as client:
        project = client.post('/v1/projects', json={'name': 'P', 'root': str(repo)}, headers=HEADERS).json()
        # Same checkout pathname now routes to a different Git administrative directory.
        (repo / '.git').rename(repo / 'original-git')
        subprocess.run(['git', 'init', '-b', 'main', '--separate-git-dir', str(tmp_path / 'other-git'), str(repo)],
                       check=True, capture_output=True)
        assert client.get('/v1/projects/' + project['id'], headers=HEADERS).status_code == 409
        assert (repo / 'user.txt').read_text() == 'preserve me'


def test_simultaneous_migration_is_idempotent(tmp_path):
    path = tmp_path / 'state.db'
    # WAL setup can itself contend on a fresh database; initialize a v1 database first.
    with sqlite3.connect(path) as db:
        db.execute('PRAGMA journal_mode=WAL')
        db.execute('CREATE TABLE agents (id TEXT PRIMARY KEY, profile TEXT NOT NULL)')
        db.execute('PRAGMA user_version=1')
    with ThreadPoolExecutor(max_workers=2) as executor:
        stores = list(executor.map(lambda _: Store(path), range(2)))
    assert all(store.list_projects() == [] for store in stores)
