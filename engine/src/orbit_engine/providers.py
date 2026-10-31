"""Provider declarations with bounded local discovery; readiness is verified separately for every local run."""
from .models import Provider
from .ollama import discover

PROVIDERS: tuple[Provider, ...] = ("claude-code", "codex-cli", "gemini-cli", "ollama")

def declarations():
    providers = [
        {"id": provider, "execution_enabled": provider == "ollama",
         "auth": "local" if provider == "ollama" else "unknown",
         "energy": {"kind": "compute" if provider == "ollama" else "shared-quota",
                    "remaining_percent": None, "status": "unknown"},
         "paid_api_fallback": False}
        for provider in PROVIDERS
    ]

    providers[-1]["execution_policy"] = "explicit-file-grants-and-local-GGUF-preflight"
    providers[-1]["discovery"] = discover()
    return providers
