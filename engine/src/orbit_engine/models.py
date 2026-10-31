from typing import Literal
from pydantic import BaseModel, Field

Provider = Literal["claude-code", "codex-cli", "gemini-cli", "ollama"]

class AgentInput(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    role: str = Field(min_length=1, max_length=120)
    seniority: str = "unspecified"
    expertise: list[str] = Field(default_factory=list)
    skills: list[str] = Field(default_factory=list)
    instructions: str = ""
    tools: list[str] = Field(default_factory=list)
    provider: Provider
    model: str = Field(min_length=1)

class Agent(AgentInput):
    id: str
