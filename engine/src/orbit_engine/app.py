import os
import secrets
from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from .models import Agent, AgentInput
from .providers import declarations
from .store import Store


def create_app(db_path: Path | None = None, token: str | None = None) -> FastAPI:
    configured_token = token if token is not None else os.environ.get("ORBIT_TOKEN", "")
    path = db_path if db_path is not None else Path(os.environ.get("ORBIT_DB", ".orbit/orbit.sqlite3"))

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        if len(configured_token) < 24 or configured_token == "replace-with-a-random-session-token":
            raise RuntimeError("Set ORBIT_TOKEN to a private random token of at least 24 characters")
        app.state.store = Store(path)
        yield

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

    @app.get("/v1/providers", dependencies=[Depends(authorize)])
    def providers():
        return declarations()

    return app

app = create_app()
