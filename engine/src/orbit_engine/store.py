from contextlib import contextmanager
import sqlite3
from pathlib import Path
from uuid import uuid4
from .models import Agent, AgentInput

class Store:
    def __init__(self, path: Path):
        self.path = path
        path.parent.mkdir(parents=True, exist_ok=True)
        with self.connect() as db:
            version = db.execute("PRAGMA user_version").fetchone()[0]
            if version not in (0, 1):
                raise RuntimeError("Unsupported database schema; refusing to overwrite")
            db.execute("PRAGMA journal_mode=WAL")
            db.execute("CREATE TABLE IF NOT EXISTS agents (id TEXT PRIMARY KEY, profile TEXT NOT NULL)")
            db.execute("PRAGMA user_version=1")

    @contextmanager
    def connect(self):
        db = sqlite3.connect(self.path, timeout=5)
        db.execute("PRAGMA foreign_keys=ON")
        try:
            with db:
                yield db
        finally:
            db.close()

    def list_agents(self) -> list[Agent]:
        with self.connect() as db:
            rows = db.execute("SELECT profile FROM agents ORDER BY rowid").fetchall()
        return [Agent.model_validate_json(row[0]) for row in rows]

    def create_agent(self, profile: AgentInput) -> Agent:
        agent = Agent(id=str(uuid4()), **profile.model_dump())
        with self.connect() as db:
            db.execute("INSERT INTO agents VALUES (?, ?)", (agent.id, agent.model_dump_json()))
        return agent
