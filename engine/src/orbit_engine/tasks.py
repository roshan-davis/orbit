"""Persistent task metadata. Execution entry points are internal, not HTTP controls."""
import json
from datetime import datetime, timezone
from typing import Literal
from uuid import uuid4
from pydantic import BaseModel, ConfigDict, Field, StrictBool, field_validator

State = Literal['queued', 'ready', 'assigned', 'running', 'awaiting_review',
                'awaiting_approval', 'completed', 'blocked', 'failed', 'cancelled']

class TaskError(Exception):
    def __init__(self, message: str, status: int = 409):
        super().__init__(message)
        self.status = status

class TaskInput(BaseModel):
    model_config = ConfigDict(extra='forbid')
    project_id: str = Field(min_length=1, max_length=120)
    title: str = Field(min_length=1, max_length=240)
    acceptance: str = Field(min_length=1, max_length=16000)
    dependencies: list[str] = Field(default_factory=list, max_length=100)

    @field_validator('title', 'acceptance')
    @classmethod
    def nonblank(cls, value):
        if not value.strip():
            raise ValueError('Must contain text')
        return value.strip()

class AssignmentInput(BaseModel):
    model_config = ConfigDict(extra='forbid')
    expected_version: int = Field(ge=0)
    agent_id: str = Field(min_length=1, max_length=120)

class ArtifactReference(BaseModel):
    model_config = ConfigDict(extra='forbid')
    label: str = Field(min_length=1, max_length=240)
    reference: str = Field(min_length=1, max_length=4096)

    @field_validator('label', 'reference')
    @classmethod
    def nonblank(cls, value):
        if not value.strip():
            raise ValueError('Artifact reference must contain text')
        return value.strip()

class TransitionInput(BaseModel):
    model_config = ConfigDict(extra='forbid')
    expected_version: int = Field(ge=0)
    state: State
    note: str = Field(min_length=1, max_length=4000)
    reviewer_id: str | None = Field(default=None, max_length=120)
    human_approval: StrictBool = False
    artifacts: list[ArtifactReference] = Field(default_factory=list, max_length=100)

    @field_validator('note')
    @classmethod
    def nonblank(cls, value):
        if not value.strip():
            raise ValueError('Audit note required')
        return value.strip()

# No terminal-state reopening; rejection returns to ready for a fresh assignment.
LEGAL = {
    'queued': {'ready', 'blocked', 'cancelled'},
    'ready': {'blocked', 'cancelled'},
    'assigned': {'running', 'blocked', 'failed', 'cancelled'},
    'running': {'awaiting_review', 'blocked', 'failed', 'cancelled'},
    'awaiting_review': {'awaiting_approval', 'ready', 'blocked', 'cancelled'},
    'awaiting_approval': {'completed', 'ready', 'blocked', 'cancelled'},
    'blocked': {'ready', 'failed', 'cancelled'},
    'failed': set(), 'cancelled': set(), 'completed': set(),
}

def migrate_tasks(db):
    # Called within Store's BEGIN IMMEDIATE migration transaction.
    db.execute('CREATE TABLE tasks (id TEXT PRIMARY KEY, project_id TEXT NOT NULL REFERENCES projects(id), '
               'title TEXT NOT NULL, acceptance TEXT NOT NULL, state TEXT NOT NULL, version INTEGER NOT NULL)')
    db.execute('CREATE TABLE task_dependencies (task_id TEXT NOT NULL REFERENCES tasks(id), '
               'dependency_id TEXT NOT NULL REFERENCES tasks(id), PRIMARY KEY(task_id, dependency_id), '
               'CHECK(task_id != dependency_id))')
    db.execute('CREATE TABLE assignments (id TEXT PRIMARY KEY, task_id TEXT NOT NULL REFERENCES tasks(id), '
               'agent_id TEXT NOT NULL REFERENCES agents(id), snapshot TEXT NOT NULL, created_at TEXT NOT NULL)')
    db.execute('CREATE TABLE task_events (sequence INTEGER PRIMARY KEY AUTOINCREMENT, '
               'task_id TEXT NOT NULL REFERENCES tasks(id), kind TEXT NOT NULL, data TEXT NOT NULL, created_at TEXT NOT NULL)')
    # API never updates events or snapshots. Database triggers also guard accidental rewrites.
    for table in ('assignments', 'task_events', 'task_dependencies'):
        for action in ('UPDATE', 'DELETE'):
            db.execute(f"CREATE TRIGGER {table}_{action.lower()} BEFORE {action} ON {table} "
                       "BEGIN SELECT RAISE(ABORT, 'immutable history'); END")
    db.execute('PRAGMA user_version=3')

class TaskStore:
    @staticmethod
    def _event(db, task_id, kind, data):
        db.execute('INSERT INTO task_events(task_id, kind, data, created_at) VALUES (?, ?, ?, ?)',
                   (task_id, kind, json.dumps(data), datetime.now(timezone.utc).isoformat()))

    @staticmethod
    def _task(db, task_id):
        row = db.execute('SELECT id, project_id, title, acceptance, state, version FROM tasks WHERE id=?', (task_id,)).fetchone()
        if not row:
            raise TaskError('Task not found', 404)
        result = dict(zip(('id', 'project_id', 'title', 'acceptance', 'state', 'version'), row))
        result['dependencies'] = [r[0] for r in db.execute('SELECT dependency_id FROM task_dependencies WHERE task_id=? ORDER BY rowid', (task_id,))]
        result['assignments'] = [dict(id=r[0], agent_id=r[1], snapshot=json.loads(r[2]), created_at=r[3]) for r in db.execute(
            'SELECT id, agent_id, snapshot, created_at FROM assignments WHERE task_id=? ORDER BY rowid', (task_id,))]
        result['events'] = [dict(sequence=r[0], kind=r[1], data=json.loads(r[2]), created_at=r[3]) for r in db.execute(
            'SELECT sequence, kind, data, created_at FROM task_events WHERE task_id=? ORDER BY sequence', (task_id,))]
        return result

    @staticmethod
    def _version(task, expected):
        if task['version'] != expected:
            raise TaskError('Task changed; refresh before retrying')

    @staticmethod
    def _dependencies_complete(db, task_id):
        if db.execute("SELECT 1 FROM task_dependencies d JOIN tasks t ON t.id=d.dependency_id WHERE d.task_id=? AND t.state!='completed' LIMIT 1", (task_id,)).fetchone():
            raise TaskError('Dependencies must be completed')

    def create_task(self, profile: TaskInput):
        # Registration is a metadata boundary only; execution must revalidate the root.
        with self.connect() as db:
            db.execute('BEGIN IMMEDIATE')
            if not db.execute('SELECT 1 FROM projects WHERE id=?', (profile.project_id,)).fetchone():
                raise TaskError('Project not found', 404)
            if len(set(profile.dependencies)) != len(profile.dependencies):
                raise TaskError('Duplicate dependencies', 422)
            for dependency in profile.dependencies:
                row = db.execute('SELECT project_id FROM tasks WHERE id=?', (dependency,)).fetchone()
                if not row or row[0] != profile.project_id:
                    raise TaskError('Dependencies must be existing tasks in this project', 422)
            task_id = str(uuid4())
            # Edges only target pre-existing tasks and cannot be edited, so cycles/self edges cannot be introduced.
            db.execute("INSERT INTO tasks VALUES (?, ?, ?, ?, 'queued', 0)", (task_id, profile.project_id, profile.title, profile.acceptance))
            db.executemany('INSERT INTO task_dependencies VALUES (?, ?)', [(task_id, d) for d in profile.dependencies])
            self._event(db, task_id, 'created', profile.model_dump())
            return self._task(db, task_id)

    def list_tasks(self, project_id):
        with self.connect() as db:
            db.execute('BEGIN')
            return [self._task(db, r[0]) for r in db.execute('SELECT id FROM tasks WHERE project_id=? ORDER BY rowid', (project_id,)).fetchall()]

    def get_task(self, task_id):
        with self.connect() as db:
            db.execute('BEGIN')
            return self._task(db, task_id)

    def assign_task(self, task_id, profile: AssignmentInput):
        with self.connect() as db:
            db.execute('BEGIN IMMEDIATE')
            task = self._task(db, task_id)
            self._version(task, profile.expected_version)
            if task['state'] != 'ready':
                raise TaskError('Only ready tasks can be assigned')
            self._dependencies_complete(db, task_id)
            row = db.execute('SELECT profile FROM agents WHERE id=?', (profile.agent_id,)).fetchone()
            if not row:
                raise TaskError('Agent not found', 404)
            assignment_id = str(uuid4())
            db.execute('INSERT INTO assignments VALUES (?, ?, ?, ?, ?)',
                       (assignment_id, task_id, profile.agent_id, row[0], datetime.now(timezone.utc).isoformat()))
            db.execute("UPDATE tasks SET state='assigned', version=version+1 WHERE id=?", (task_id,))
            self._event(db, task_id, 'assigned', {'assignment_id': assignment_id, 'agent_id': profile.agent_id})
            return self._task(db, task_id)

    def transition_task(self, task_id, action: TransitionInput, *, execution=False):
        with self.connect() as db:
            db.execute('BEGIN IMMEDIATE')
            task = self._task(db, task_id)
            self._version(task, action.expected_version)
            old, new = task['state'], action.state
            if new not in LEGAL[old]:
                raise TaskError('Illegal task transition')
            if new in ('running', 'awaiting_review') and not execution:
                raise TaskError('Execution transitions require a worker; execution is not enabled')
            # HTTP metadata cancellation/blocking must not pretend to stop a live worker.
            if old == 'running' and not execution:
                raise TaskError('Running task changes require worker coordination')
            if new in ('ready', 'running'):
                self._dependencies_complete(db, task_id)
            if new == 'awaiting_review' and not action.artifacts:
                raise TaskError('Review requires artifact references')
            if action.artifacts and new != 'awaiting_review':
                raise TaskError('Artifact references belong to execution completion')
            data = {'from': old, 'to': new, 'note': action.note}
            if action.artifacts:
                data['artifacts'] = [artifact.model_dump() for artifact in action.artifacts]

            if new == 'awaiting_approval' or (old == 'awaiting_review' and new == 'ready'):
                if not task['assignments'] or not action.reviewer_id:
                    raise TaskError('Independent reviewer required')
                # All authors of this task, including earlier revisions, are excluded.
                if action.reviewer_id in {a['agent_id'] for a in task['assignments']}:
                    raise TaskError('Reviewer must be distinct from task authors')
                reviewer = db.execute('SELECT profile FROM agents WHERE id=?', (action.reviewer_id,)).fetchone()
                if not reviewer:
                    raise TaskError('Reviewer not found', 404)
                data.update(reviewer_id=action.reviewer_id, reviewer_snapshot=json.loads(reviewer[0]),
                            assignment_id=task['assignments'][-1]['id'])
            if new == 'completed':
                if not action.human_approval:
                    raise TaskError('Explicit human approval required')
                data['human_approval'] = True
            db.execute('UPDATE tasks SET state=?, version=version+1 WHERE id=?', (new, task_id))
            self._event(db, task_id, 'transition', data)
            return self._task(db, task_id)
