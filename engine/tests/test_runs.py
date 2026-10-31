import json
import sqlite3
import subprocess
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError
from orbit_engine.app import create_app
from orbit_engine.store import Store
from orbit_engine.models import AgentInput, ProjectInput
from orbit_engine.tasks import TaskInput, AssignmentInput, TransitionInput, TaskError
from orbit_engine.runs import Runner, RunInput, safe_file, read_text
from orbit_engine.local_model import LocalModel
from test_api import TOKEN, HEADERS, PROFILE

class FakeModel:
    def verify(self, model, stopped):
        return 'local-weights'
    def generate(self, model, prompt, stopped):
        return {'files': [{'path': 'hello.txt', 'content': 'after\n'}]}
    def cancel(self):
        pass

@pytest.fixture
def mission(tmp_path):
    root=tmp_path/'repo'; root.mkdir()
    def git(*args):
        return subprocess.check_output(['git','-C',str(root),*args], text=True)
    git('init', '-q'); git('config','user.email','test@example.invalid'); git('config','user.name','Test')
    (root/'hello.txt').write_text('before\n')
    git('add','.'); git('commit','-qm','base')
    (root/'staged.txt').write_text('staged'); git('add','staged.txt')
    (root/'hello.txt').write_text('primary dirty\n')
    (root/'untracked.txt').write_text('keep')
    store=Store(tmp_path/'db.sqlite')
    project=store.create_project(ProjectInput(name='Repo',root=str(root)))
    agent=store.create_agent(AgentInput(**{**PROFILE,'provider':'ollama','model':'local-model'}))
    task=store.create_task(TaskInput(project_id=project.id,title='Edit hello',acceptance='after'))
    task=store.transition_task(task['id'],TransitionInput(expected_version=0,state='ready',note='Ready'))
    task=store.assign_task(task['id'],AssignmentInput(expected_version=1,agent_id=agent.id))
    parent=tmp_path/'trees'; parent.mkdir()
    grant=RunInput(expected_version=2,approved_parent=str(parent),files=['hello.txt'],grant_file_access=True)
    return store, task, grant, root, git

def wait(runner):
    deadline=time.monotonic()+5
    while runner.active and time.monotonic()<deadline:
        time.sleep(.01)
    assert runner.active is None


def test_real_worktree_fixture_produces_diff_preserves_primary_and_persists(mission):
    store,task,grant,root,git=mission
    status=git('status','--porcelain=v1'); runner=Runner(store,FakeModel)
    try:
        runner.start(task['id'],grant); wait(runner)
        run=runner.get(task['id'])[0]
        assert run['status']=='awaiting_review'
        assert '+after' in run['diff'] and '-before' in run['diff']
        assert Path(run['path'],'hello.txt').read_text()=='after\n'
        assert git('status','--porcelain=v1')==status
        assert (root/'hello.txt').read_text()=='primary dirty\n'
        assert (root/'untracked.txt').read_text()=='keep'
        assert len(run['logs'])<=12
        with pytest.raises(TaskError): runner.start(task['id'],grant)
    finally: runner.close()
    reopened=Runner(Store(store.path),FakeModel)
    assert reopened.get(task['id'])==[run]
    assert store.get_task(task['id'])['state']=='awaiting_review'
    reopened.close()


class Paused(FakeModel):
    entered=threading.Event()
    release=threading.Event()
    def generate(self,model,prompt,stopped):
        self.entered.set(); self.release.wait(4)
        return super().generate(model,prompt,stopped)
    def cancel(self): self.release.set()


def test_cancel_no_writes_after_response_and_one_concurrent_start(mission):
    store,task,grant,_,_=mission
    Paused.entered.clear(); Paused.release.clear()
    runner=Runner(store,Paused)
    def start(_):
        try: runner.start(task['id'],grant); return 'ok'
        except TaskError: return 'conflict'
    try:
        with ThreadPoolExecutor(2) as pool: assert sorted(pool.map(start,range(2)))==['conflict','ok']
        assert Paused.entered.wait(2)
        with pytest.raises(TaskError): runner.cancel(task['id'], 'stale-run')
        runner.cancel(task['id'], runner.get(task['id'])[-1]['id']); wait(runner)
        run=runner.get(task['id'])[0]
        assert run['status']=='cancelled' and run['diff']==''
        assert Path(run['path'],'hello.txt').read_text()=='before\n'
        assert store.get_task(task['id'])['state']=='cancelled'
    finally: Paused.release.set(); runner.close()


def test_restart_interrupts_without_duplicate_execution_and_second_owner_fails(mission):
    store,task,grant,_,_=mission
    runner=Runner(store,FakeModel)
    with pytest.raises(RuntimeError,match='Another engine'): Runner(store,FakeModel)
    runner.close()
    with store.connect() as db:
        assignment=task['assignments'][-1]['id']
        db.execute("INSERT INTO runs VALUES ('old',?,?, 'running','{}','[]','')",(task['id'],assignment))
        db.execute("UPDATE tasks SET state='running',version=3 WHERE id=?",(task['id'],))
    runner=Runner(Store(store.path),FakeModel)
    assert store.get_task(task['id'])['state']=='failed'
    assert runner.get(task['id'])[0]['status']=='failed'
    assert 'no automatic retry' in runner.get(task['id'])[0]['logs'][-1]
    with pytest.raises(TaskError): runner.start(task['id'],grant)
    runner.close()

@pytest.mark.parametrize('output',[
    {}, {'files':[]}, {'files':[{'path':'../escape','content':'oops'}]},
    {'files':[{'path':'other.txt','content':'oops'}]},
    {'files':[{'path':'hello.txt','content':'x'*65537}]},
    {'files':[{'path':'hello.txt','content':'same'},{'path':'hello.txt','content':'again'}]},
    {'files':[{'path':'hello.txt','content':'before\n'}]},
    {'files':[{'path':'hello.txt','content':'\0'}]},
])
def test_bad_response_never_applies_file_edits(mission,output):
    store,task,grant,_,_=mission
    class Bad(FakeModel):
        def generate(self,*args): return output
    runner=Runner(store,Bad)
    try:
        runner.start(task['id'],grant); wait(runner)
        run=runner.get(task['id'])[0]
        assert run['status']=='failed'
        assert Path(run['path'],'hello.txt').read_text()=='before\n'
    finally: runner.close()

@pytest.mark.parametrize('name',['../oops','.git/config','a/../b','/etc/passwd','a//b','.env','secrets/key','api-token.txt'])
def test_invalid_grant_names(name):
    with pytest.raises(ValidationError): RunInput(expected_version=2,approved_parent='/tmp',files=[name],grant_file_access=True)


def test_symlink_hardlink_binary_and_credentials_fail_closed(tmp_path):
    root=tmp_path/'root';root.mkdir(); outside=tmp_path/'outside';outside.write_text('keep')
    (root/'link').symlink_to(outside)
    with pytest.raises(TaskError): safe_file(root,'link')
    import os
    os.link(outside,root/'hard')
    with pytest.raises(TaskError): safe_file(root,'hard')
    path=root/'text';path.write_bytes(b'\0')
    with pytest.raises(TaskError): read_text(path)
    path.write_text('api_key=not-a-real-test-secret')
    with pytest.raises(TaskError): read_text(path)


def test_v3_migration_rollback(mission):
    store,*_=mission
    with store.connect() as db:
        db.execute('PRAGMA user_version=3')
    with pytest.raises(sqlite3.OperationalError): Store(store.path)
    with store.connect() as db:
        assert db.execute('PRAGMA user_version').fetchone()[0]==3


def test_api_auth_and_explicit_grants(mission,monkeypatch):
    store,task,grant,_,_=mission
    monkeypatch.setattr('orbit_engine.runs.LocalModel',FakeModel)
    with TestClient(create_app(store.path,TOKEN)) as client:
        # Inject deterministic fixture, never contact a live server.
        client.app.state.runner.model_factory=FakeModel
        route='/v1/tasks/'+task['id']+'/runs'
        for method,url,body in [('get',route,None),('post',route,grant.model_dump()),('post',route+'/cancel',{})]:
            assert getattr(client,method)(url,**({'json':body} if body is not None else {})).status_code==401
        assert client.post(route,json={**grant.model_dump(),'grant_file_access':False},headers=HEADERS).status_code==409
        assert client.post(route,json={**grant.model_dump(),'files':['../escape']},headers=HEADERS).status_code==422
        assert client.post(route,json=grant.model_dump(),headers=HEADERS).status_code==202
        wait(client.app.state.runner)
        assert client.get(route,headers=HEADERS).json()[0]['status']=='awaiting_review'


def test_local_model_preflight_and_json_contract(tmp_path,monkeypatch):
    local=LocalModel(); stopped=threading.Event()
    blob=tmp_path/('sha256-'+'a'*64);blob.write_bytes(b'GGUFtest')
    info={'modelfile':'FROM '+str(blob),'capabilities':['completion']}
    monkeypatch.setattr(local,'request',lambda *args:info)
    assert local.verify('gemma-local',stopped)==blob.name
    for bad in [{**info,'remote_model':'cloud'}, {**info,'remote_host':'host'},
                {**info,'capabilities':['embedding']},{**info,'modelfile':'FROM cloud'}]:
        monkeypatch.setattr(local,'request',lambda *args:bad)
        with pytest.raises(TaskError):local.verify('gemma-local',stopped)
    for name in ['gemma:cloud','bad name','-option']:
        with pytest.raises(TaskError):local.verify(name,stopped)
    monkeypatch.setattr(local,'request',lambda *args:{'done':True,'done_reason':'length','message':{'content':'{}'}})
    with pytest.raises(TaskError):local.generate('local','prompt',stopped)

@pytest.mark.parametrize('status,body',[(302,b'{}'),(500,b'private server body'),(200,b'not json'),(200,b'[]'),(200,b'x'*262145)])
def test_transport_rejects_redirect_error_malformed_and_oversized(monkeypatch,status,body):
    calls=[]
    class Response:
        def __init__(self):self.status=status;self.offset=0
        def read1(self,n):
            chunk=body[self.offset:self.offset+n];self.offset+=len(chunk);return chunk
    class Connection:
        sock=None
        def __init__(self,*args,**kwargs):calls.append(args)
        def request(self,*args):calls.append(args)
        def getresponse(self):return Response()
        def close(self):pass
    monkeypatch.setattr('orbit_engine.local_model._LocalConnection',Connection)
    monkeypatch.setenv('OLLAMA_HOST','https://example.invalid')
    with pytest.raises(TaskError) as error: LocalModel().request('/api/show',{'model':'local'},threading.Event())
    assert 'private server body' not in str(error.value)
    assert calls[0]==('127.0.0.1',11434)
    assert calls[1][0:2]==('POST','/api/show')
    assert 'Authorization' not in calls[1][3]


def test_cancellation_survives_restart(mission):
    store,task,grant,_,_=mission
    with store.connect() as db:
        db.execute("INSERT INTO runs VALUES ('cancel',?,?, 'cancelling','{}','[]','')",(task['id'],task['assignments'][-1]['id']))
        db.execute("UPDATE tasks SET state='running' WHERE id=?",(task['id'],))
    runner=Runner(store,FakeModel)
    try:
        assert runner.get(task['id'])[0]['status']=='cancelled'
        assert store.get_task(task['id'])['state']=='cancelled'
    finally:runner.close()


def test_preflight_failure_is_recorded_without_worktree(mission):
    store,task,grant,_,_=mission
    class Fails(FakeModel):
        def verify(self,*args):raise TaskError('Local model unavailable')
    runner=Runner(store,Fails)
    try:
        runner.start(task['id'],grant);wait(runner)
        run=runner.get(task['id'])[0]
        assert run['status']=='failed' and not Path(run['path']).exists()
        assert 'Local model unavailable' in run['logs'][-1]
        assert store.get_task(task['id'])['state']=='failed'
    finally:runner.close()
