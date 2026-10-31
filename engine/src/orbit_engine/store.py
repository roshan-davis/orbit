from contextlib import contextmanager
import sqlite3
from pathlib import Path
from uuid import uuid4
from .models import Agent, AgentInput, Project, ProjectInput
from .projects import ProjectError, inspect_project

from .tasks import TaskStore, migrate_tasks

class Store(TaskStore):
    def __init__(self, path: Path):
        self.path = path
        path.parent.mkdir(parents=True, exist_ok=True)
        with self.connect() as db:
            version = db.execute("PRAGMA user_version").fetchone()[0]
            if version not in (0, 1, 2, 3):
                raise RuntimeError("Unsupported database schema; refusing to overwrite")
            db.execute("PRAGMA journal_mode=WAL")
            # Explicit BEGIN makes DDL and version advancement roll back together.
            db.execute("BEGIN IMMEDIATE")
            version = db.execute("PRAGMA user_version").fetchone()[0]
            if version not in (0, 1, 2, 3):
                raise RuntimeError("Unsupported database schema; refusing to overwrite")
            if version == 0:
                db.execute("CREATE TABLE IF NOT EXISTS agents (id TEXT PRIMARY KEY, profile TEXT NOT NULL)")
                db.execute("PRAGMA user_version=1")
                version = 1
            if version == 1:
                db.execute("CREATE TABLE projects (id TEXT PRIMARY KEY, name TEXT NOT NULL, "
                           "root TEXT NOT NULL UNIQUE, git_directory TEXT NOT NULL, "
                           "common_directory TEXT NOT NULL)")
                db.execute("PRAGMA user_version=2")
                version = 2
            if version == 2:
                migrate_tasks(db)

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

    def get_agent(self, agent_id: str) -> Agent | None:
        with self.connect() as db:
            row = db.execute("SELECT profile FROM agents WHERE id = ?", (agent_id,)).fetchone()
        return Agent.model_validate_json(row[0]) if row else None

    def update_agent(self, agent_id: str, profile: AgentInput) -> Agent | None:
        agent = Agent(id=agent_id, **profile.model_dump())
        with self.connect() as db:
            result = db.execute("UPDATE agents SET profile = ? WHERE id = ?",
                                (agent.model_dump_json(), agent_id))
            return agent if result.rowcount else None

    def list_projects(self) -> list[Project]:
        with self.connect() as db:
            rows = db.execute("SELECT id, name, root, git_directory, common_directory "
                              "FROM projects ORDER BY rowid").fetchall()
        return [self._project(row) for row in rows]

    @staticmethod
    def _project(row) -> Project:
        return Project(**dict(zip(
            ("id", "name", "root", "git_directory", "common_directory"), row)))

    def create_project(self, profile: ProjectInput) -> Project:
        inspected = inspect_project(profile.root)
        project = Project(id=str(uuid4()), name=profile.name, root=str(inspected.root),
                          git_directory=str(inspected.git_directory),
                          common_directory=str(inspected.common_directory))
        with self.connect() as db:
            db.execute("INSERT INTO projects (id, name, root, git_directory, common_directory) "
                       "VALUES (?, ?, ?, ?, ?)",
                       (project.id, project.name, project.root, project.git_directory,
                        project.common_directory))
        return project

    def get_project(self, project_id: str) -> Project | None:
        with self.connect() as db:
            row = db.execute("SELECT id, name, root, git_directory, common_directory "
                             "FROM projects WHERE id = ?", (project_id,)).fetchone()
        if row is None:
            return None
        project = self._project(row)
        inspected = inspect_project(project.root)
        if (str(inspected.git_directory), str(inspected.common_directory)) != (
                project.git_directory, project.common_directory):
            raise ProjectError("Registered checkout identity changed; inspect repository state")
        return project
