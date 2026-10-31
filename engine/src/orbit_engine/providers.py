"""Capability declarations only. No credentials or subprocesses are accessed."""
from .models import Provider

PROVIDERS: tuple[Provider, ...] = ("claude-code", "codex-cli", "gemini-cli", "ollama")

def declarations():
    return [
        {"id": provider, "execution_enabled": False,
         "auth": "local" if provider == "ollama" else "unknown",
         "energy": {"kind": "compute" if provider == "ollama" else "shared-quota",
                    "remaining_percent": None, "status": "unknown"},
         "paid_api_fallback": False}
        for provider in PROVIDERS
    ]
