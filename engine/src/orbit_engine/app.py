import os
import secrets
import sqlite3
from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from .models import Agent, AgentInput, Project, ProjectInput
from .projects import ProjectError
from .providers import declarations
from .store import Store
from .runs import Runner, RunInput, CancelInput
from .tasks import TaskError, TaskInput, AssignmentInput, TransitionInput
from fastapi.responses import JSONResponse


def create_app(db_path: Path | None = None, token: str | None = None) -> FastAPI:
    configured_token = token if token is not None else os.environ.get("ORBIT_TOKEN", "")
    path = db_path if db_path is not None else Path(os.environ.get("ORBIT_DB", ".orbit/orbit.sqlite3"))

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        if len(configured_token) < 24 or configured_token == "replace-with-a-random-session-token":
            raise RuntimeError("Set ORBIT_TOKEN to a private random token of at least 24 characters")
        app.state.store = Store(path)
        app.state.runner = Runner(app.state.store)
        try:
            yield
        finally:
            app.state.runner.close()

    app = FastAPI(title="Orbit Engine", version="0.1.0", lifespan=lifespan)
    app.add_middleware(CORSMiddleware,
        allow_origins=["http://localhost:1420", "http://127.0.0.1:1420",
                       "tauri://localhost", "http://tauri.localhost", "https://tauri.localhost"],
        allow_methods=["GET", "POST", "PUT"], allow_headers=["Authorization", "Content-Type"])
    bearer = HTTPBearer(auto_error=False)

    def authorize(credentials: HTTPAuthorizationCredentials | None = Depends(bearer)):
        if not credentials or not secrets.compare_digest(credentials.credentials.encode(), configured_token.encode()):
            raise HTTPException(status_code=401, detail="Valid engine token required")

    @app.get("/health")
    def health():
        return {"status": "ok", "service": "orbit-engine"}

    @app.get("/v1/agents", response_model=list[Agent], dependencies=[Depends(authorize)])
    def list_agents():
        return app.state.store.list_agents()

    @app.post("/v1/agents", response_model=Agent, status_code=201, dependencies=[Depends(authorize)])
    def create_agent(profile: AgentInput):
        return app.state.store.create_agent(profile)

    @app.get("/v1/agents/{agent_id}", response_model=Agent, dependencies=[Depends(authorize)])
    def get_agent(agent_id: str):
        agent = app.state.store.get_agent(agent_id)
        if agent is None:
            raise HTTPException(status_code=404, detail="Agent not found")
        return agent

    @app.put("/v1/agents/{agent_id}", response_model=Agent, dependencies=[Depends(authorize)])
    def update_agent(agent_id: str, profile: AgentInput):
        agent = app.state.store.update_agent(agent_id, profile)
        if agent is None:
            raise HTTPException(status_code=404, detail="Agent not found")
        return agent

    @app.get("/v1/projects", response_model=list[Project], dependencies=[Depends(authorize)])
    def list_projects():
        return app.state.store.list_projects()

    @app.post("/v1/projects", response_model=Project, status_code=201, dependencies=[Depends(authorize)])
    def create_project(profile: ProjectInput):
        try:
            return app.state.store.create_project(profile)
        except ProjectError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc
        except sqlite3.IntegrityError as exc:
            raise HTTPException(status_code=409, detail="Project root already registered") from exc

    @app.get("/v1/projects/{project_id}", response_model=Project, dependencies=[Depends(authorize)])
    def get_project(project_id: str):
        try:
            project = app.state.store.get_project(project_id)
        except ProjectError as exc:
            raise HTTPException(status_code=409, detail="Registered project unavailable; check its canonical root") from exc
        if project is None:
            raise HTTPException(status_code=404, detail="Project not found")
        return project

    @app.exception_handler(TaskError)
    async def task_error(_request, exc):
        return JSONResponse(status_code=exc.status, content={"detail": str(exc)})

    @app.post("/v1/tasks", status_code=201, dependencies=[Depends(authorize)])
    def create_task(profile: TaskInput):
        return app.state.store.create_task(profile)

    @app.get("/v1/tasks", dependencies=[Depends(authorize)])
    def list_tasks(project_id: str):
        return app.state.store.list_tasks(project_id)

    @app.get("/v1/tasks/{task_id}", dependencies=[Depends(authorize)])
    def get_task(task_id: str):
        return app.state.store.get_task(task_id)

    @app.post("/v1/tasks/{task_id}/assignments", dependencies=[Depends(authorize)])
    def assign_task(task_id: str, profile: AssignmentInput):
        return app.state.store.assign_task(task_id, profile)

    @app.post("/v1/tasks/{task_id}/transitions", dependencies=[Depends(authorize)])
    def transition_task(task_id: str, profile: TransitionInput):
        return app.state.store.transition_task(task_id, profile)

    @app.get("/v1/tasks/{task_id}/runs", dependencies=[Depends(authorize)])
    def get_runs(task_id: str):
        return app.state.runner.get(task_id)

    @app.post("/v1/tasks/{task_id}/runs", status_code=202, dependencies=[Depends(authorize)])
    def start_run(task_id: str, profile: RunInput):
        try:
            return app.state.runner.start(task_id, profile)
        except ProjectError as exc:
            raise TaskError('Project or worktree parent unavailable; verify canonical paths') from exc

    @app.post("/v1/tasks/{task_id}/runs/cancel", dependencies=[Depends(authorize)])
    def cancel_run(task_id: str, profile: CancelInput):
        return app.state.runner.cancel(task_id, profile.run_id)

    @app.get("/v1/providers", dependencies=[Depends(authorize)])
    def providers():
        return declarations()

    return app

app = create_app()
