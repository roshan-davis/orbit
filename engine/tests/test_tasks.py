import json
import sqlite3
from concurrent.futures import ThreadPoolExecutor
import pytest
from fastapi.testclient import TestClient
from orbit_engine.app import create_app
from orbit_engine.store import Store
from orbit_engine.models import AgentInput
from orbit_engine.tasks import TaskInput, AssignmentInput, TransitionInput, TaskError, LEGAL
from test_api import TOKEN, HEADERS, PROFILE

@pytest.fixture
def setup(tmp_path):
    store = Store(tmp_path / 'state.db')
    # Registry behavior is covered separately; task tests need only registered identities.
    with store.connect() as db:
        db.executemany('INSERT INTO projects VALUES (?, ?, ?, ?, ?)',
                       [('p', 'Project', '/not-accessed', '/git', '/git'),
                        ('other', 'Other', '/other', '/other/.git', '/other/.git')])
    author = store.create_agent(AgentInput(**PROFILE, instructions='Original', skills=['review@v1'], tools=['read']))
    reviewer = store.create_agent(AgentInput(**{**PROFILE, 'name': 'Reviewer'}))
    return store, author, reviewer

def create(store, dependencies=None, project='p'):
    return store.create_task(TaskInput(project_id=project, title='Task', acceptance='Tests pass', dependencies=dependencies or []))

def move(store, task, state, **extra):
    return store.transition_task(task['id'], TransitionInput(expected_version=task['version'], state=state, note='Evidence', **extra), execution=True)

def assigned(store, author):
    task = move(store, create(store), 'ready')
    return store.assign_task(task['id'], AssignmentInput(expected_version=task['version'], agent_id=author.id))

def reviewable(store, author):
    task = move(store, assigned(store, author), 'running')
    return move(store, task, 'awaiting_review', artifacts=[{'label': 'Diff', 'reference': 'local-review/diff'}])

def test_snapshots_events_and_restart(setup):
    store, author, _ = setup
    task = assigned(store, author)
    store.update_agent(author.id, AgentInput(**{**PROFILE, 'provider': 'codex-cli', 'model': 'other'}))
    reopened = Store(store.path).get_task(task['id'])
    assert reopened == task
    snapshot = reopened['assignments'][0]['snapshot']
    assert snapshot == author.model_dump()
    assert snapshot['instructions'] == 'Original' and snapshot['skills'] == ['review@v1'] and snapshot['tools'] == ['read']
    assert [e['kind'] for e in task['events']] == ['created', 'transition', 'assigned']
    with store.connect() as db:
        for table in ('assignments', 'task_events', 'task_dependencies'):
            for operation in (f'DELETE FROM {table}', f'UPDATE {table} SET '+ {'assignments': 'agent_id=agent_id', 'task_events': 'kind=kind', 'task_dependencies': 'task_id=task_id'}[table]):
                if table == 'task_dependencies':
                    continue  # tested with an actual edge below
                with pytest.raises(sqlite3.IntegrityError, match='immutable'):
                    db.execute(operation)

def test_dependencies_are_immutable_existing_same_project_and_complete(setup):
    store, author, reviewer = setup
    dep = create(store)
    child = create(store, [dep['id']])
    for ids in (['missing'], [dep['id'], dep['id']], [create(store, project='other')['id']]):
        with pytest.raises(TaskError):
            create(store, ids)
    before = store.get_task(child['id'])
    with pytest.raises(TaskError, match='Dependencies'):
        move(store, child, 'ready')
    assert store.get_task(child['id']) == before
    # Cycle/self injection through editing is unavailable; SQL self-edges also fail.
    with store.connect() as db:
        with pytest.raises(sqlite3.IntegrityError):
            db.execute('INSERT INTO task_dependencies VALUES (?, ?)', (child['id'], child['id']))
        with pytest.raises(sqlite3.IntegrityError):
            db.execute('DELETE FROM task_dependencies WHERE task_id=?', (child['id'],))
    dep = move(store, dep, 'ready')
    dep = store.assign_task(dep['id'], AssignmentInput(expected_version=dep['version'], agent_id=author.id))
    dep = move(store, dep, 'running')
    dep = move(store, dep, 'awaiting_review', artifacts=[{'label': 'Tests', 'reference': 'test-report'}])
    dep = move(store, dep, 'awaiting_approval', reviewer_id=reviewer.id)
    dep = move(store, dep, 'completed', human_approval=True)
    assert move(store, child, 'ready')['state'] == 'ready'

@pytest.mark.parametrize('terminal', ['failed', 'cancelled'])
def test_failed_or_cancelled_dependency_never_unblocks(setup, terminal):
    store, author, _ = setup
    dep = assigned(store, author)
    child = create(store, [dep['id']])
    move(store, dep, terminal)
    with pytest.raises(TaskError, match='Dependencies'):
        move(store, child, 'ready')

def test_review_approval_revision_and_artifact_gates(setup):
    store, author, reviewer = setup
    running = move(store, assigned(store, author), 'running')
    with pytest.raises(TaskError, match='artifact'):
        move(store, running, 'awaiting_review')
    task = move(store, running, 'awaiting_review', artifacts=[{'label': 'Diff', 'reference': 'diff'}])
    for actor in (None, author.id, 'missing'):
        with pytest.raises(TaskError):
            move(store, task, 'awaiting_approval', reviewer_id=actor)
        assert store.get_task(task['id']) == task
    task = move(store, task, 'ready', reviewer_id=reviewer.id)  # rejection
    task = store.assign_task(task['id'], AssignmentInput(expected_version=task['version'], agent_id=author.id))
    assert len(task['assignments']) == 2
    with pytest.raises(TaskError):
        move(store, task, 'completed', human_approval=True)
    task = move(store, task, 'running')
    task = move(store, task, 'awaiting_review', artifacts=[{'label': 'Diff', 'reference': 'revised-diff'}])
    task = move(store, task, 'awaiting_approval', reviewer_id=reviewer.id)
    assert task['events'][-1]['data']['assignment_id'] == task['assignments'][-1]['id']
    with pytest.raises(TaskError, match='human approval'):
        move(store, task, 'completed')
    task = move(store, task, 'completed', human_approval=True)
    assert task['events'][-1]['data']['human_approval'] is True
    with pytest.raises(TaskError):
        move(store, task, 'ready')

@pytest.mark.parametrize('old', list(LEGAL))
@pytest.mark.parametrize('new', list(LEGAL))
def test_transition_matrix(setup, old, new):
    store, author, reviewer = setup
    task = assigned(store, author)
    # Seed each source state to exercise the complete adjacency matrix independently.
    with store.connect() as db:
        db.execute('UPDATE tasks SET state=? WHERE id=?', (old, task['id']))
    task = store.get_task(task['id'])
    kwargs = {'reviewer_id': reviewer.id, 'human_approval': True}
    if new == 'awaiting_review':
        kwargs['artifacts'] = [{'label': 'Diff', 'reference': 'diff'}]
    if new in LEGAL[old]:
        assert move(store, task, new, **kwargs)['state'] == new
    else:
        with pytest.raises(TaskError, match='Illegal'):
            move(store, task, new, **kwargs)
        assert store.get_task(task['id']) == task

def test_concurrent_assignment_and_transition_have_one_winner(setup):
    store, author, _ = setup
    task = create(store)
    def ready(_):
        try:
            move(store, task, 'ready')
            return 'ok'
        except TaskError:
            return 'conflict'
    with ThreadPoolExecutor(max_workers=2) as executor:
        assert sorted(executor.map(ready, range(2))) == ['conflict', 'ok']
    task = store.get_task(task['id'])
    def assign(_):
        try:
            store.assign_task(task['id'], AssignmentInput(expected_version=task['version'], agent_id=author.id))
            return 'ok'
        except TaskError:
            return 'conflict'
    with ThreadPoolExecutor(max_workers=2) as executor:
        assert sorted(executor.map(assign, range(2))) == ['conflict', 'ok']
    result = store.get_task(task['id'])
    assert len(result['assignments']) == 1 and len(result['events']) == 3

def test_event_failure_rolls_back_assignment_and_transition(setup, monkeypatch):
    store, author, _ = setup
    task = create(store)
    original = store._event
    def broken(*args):
        raise RuntimeError('injected failure')
    monkeypatch.setattr(store, '_event', broken)
    with pytest.raises(RuntimeError):
        move(store, task, 'ready')
    assert store.get_task(task['id']) == task
    monkeypatch.setattr(store, '_event', original)
    task = move(store, task, 'ready')
    monkeypatch.setattr(store, '_event', broken)
    with pytest.raises(RuntimeError):
        store.assign_task(task['id'], AssignmentInput(expected_version=task['version'], agent_id=author.id))
    assert store.get_task(task['id']) == task

def test_migration_v2_preserves_data_and_rolls_back_failure(tmp_path):
    path = tmp_path / 'old.db'
    with sqlite3.connect(path) as db:
        db.execute('CREATE TABLE agents (id TEXT PRIMARY KEY, profile TEXT NOT NULL)')
        db.execute('CREATE TABLE projects (id TEXT PRIMARY KEY, name TEXT NOT NULL, root TEXT NOT NULL UNIQUE, git_directory TEXT NOT NULL, common_directory TEXT NOT NULL)')
        db.execute('INSERT INTO projects VALUES (\'p\', \'Project\', \'/root\', \'/git\', \'/git\')')
        db.execute('INSERT INTO agents VALUES (?, ?)', ('a', json.dumps({**PROFILE, 'id': 'a'})))
        db.execute('PRAGMA user_version=2')
        db.execute('CREATE TABLE assignments (sentinel TEXT)')
    with pytest.raises(sqlite3.OperationalError):
        Store(path)
    with sqlite3.connect(path) as db:
        assert db.execute('PRAGMA user_version').fetchone()[0] == 2
        assert not db.execute("SELECT name FROM sqlite_master WHERE name='tasks'").fetchall()
        db.execute('DROP TABLE assignments')
    for _ in range(2):
        store = Store(path)
        assert store.list_agents()[0].id == 'a'
        assert store.list_projects()[0].id == 'p'
    with store.connect() as db:
        assert db.execute('PRAGMA user_version').fetchone()[0] == 3

def test_task_api_auth_validation_and_worker_boundary(setup):
    store, author, _ = setup
    with TestClient(create_app(store.path, TOKEN)) as client:
        body = {'project_id': 'p', 'title': 'Task', 'acceptance': 'Pass'}
        for method, route, data in [('get', '/v1/tasks?project_id=p', None), ('get', '/v1/tasks/missing', None),
             ('post', '/v1/tasks', body), ('post', '/v1/tasks/missing/assignments', {'agent_id': author.id, 'expected_version': 0}),
             ('post', '/v1/tasks/missing/transitions', {'expected_version': 0, 'state': 'ready', 'note': 'Ready'})]:
            for headers in ({}, {'Authorization': 'Bearer wrong'}):
                assert getattr(client, method)(route, headers=headers, **({'json': data} if data else {})).status_code == 401
        assert client.post('/v1/tasks', json={**body, 'title': '  '}, headers=HEADERS).status_code == 422
        assert client.post('/v1/tasks', json={**body, 'project_id': 'missing'}, headers=HEADERS).status_code == 404
        response = client.post('/v1/tasks', json=body, headers=HEADERS)
        assert response.status_code == 201
        task = response.json()
        base = '/v1/tasks/' + task['id']
        assert client.get(base, headers=HEADERS).json() == task
        assert client.get('/v1/tasks?project_id=other', headers=HEADERS).json() == []
        assert client.get('/v1/tasks?project_id=p', headers=HEADERS).json()[-1] == task
        assert client.post(base+'/transitions', json={'state': 'ready', 'note': 'Go', 'expected_version': 0}, headers=HEADERS).status_code == 200
        assert client.post(base+'/assignments', json={'agent_id': 'missing', 'expected_version': 1}, headers=HEADERS).status_code == 404
        assert client.post(base+'/assignments', json={'agent_id': author.id, 'expected_version': 1}, headers=HEADERS).status_code == 200
        for state in ('running', 'completed'):
            assert client.post(base+'/transitions', json={'state': state, 'note': 'Cannot forge work', 'expected_version': 2, 'human_approval': True}, headers=HEADERS).status_code == 409
        running = move(store, store.get_task(task['id']), 'running')
        assert client.post(base+'/transitions', json={'state': 'cancelled', 'note': 'Not a process cancel', 'expected_version': running['version']}, headers=HEADERS).status_code == 409

@pytest.mark.parametrize('list_view', [False, True])
def test_reads_have_one_snapshot_during_concurrent_transition(setup, monkeypatch, list_view):
    from contextlib import contextmanager
    store, _, _ = setup
    task = create(store)
    original = store.connect
    fired = False
    @contextmanager
    def interleaved():
        nonlocal fired
        with original() as db:
            def trace(sql):
                nonlocal fired
                if not fired and sql.startswith('SELECT dependency_id'):
                    fired = True
                    # WAL allows the writer to commit while the reader retains its snapshot.
                    move(store, task, 'ready')
            db.set_trace_callback(trace)
            yield db
    monkeypatch.setattr(store, 'connect', interleaved)
    observed = store.list_tasks('p')[0] if list_view else store.get_task(task['id'])
    assert fired
    assert observed == task
    assert store.get_task(task['id'])['state'] == 'ready'
