from typing import Literal
from pydantic import BaseModel, Field, field_validator

Provider = Literal["claude-code", "codex-cli", "gemini-cli", "ollama"]

class AgentProfile(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    role: str = Field(min_length=1, max_length=120)
    seniority: str = "unspecified"
    expertise: list[str] = Field(default_factory=list)
    skills: list[str] = Field(default_factory=list)
    instructions: str = ""
    tools: list[str] = Field(default_factory=list)
    provider: Provider
    model: str = Field(min_length=1)

class AgentInput(AgentProfile):
    @field_validator("name", "role", "seniority", "model")
    @classmethod
    def meaningful_identity(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Must contain non-whitespace characters")
        return value

class Agent(AgentProfile):
    id: str


class ProjectInput(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    root: str = Field(min_length=1, max_length=4096)

    @field_validator("name")
    @classmethod
    def meaningful_name(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Must contain non-whitespace characters")
        return value


class Project(ProjectInput):
    id: str
    git_directory: str
    common_directory: str
