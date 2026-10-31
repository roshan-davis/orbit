"""Provider API tests never require or contact a live local model server."""
import pytest
from orbit_engine import ollama


@pytest.fixture(autouse=True)
def offline_ollama_by_default(monkeypatch):
    class OfflineConnection:
        def __init__(self, *args, **kwargs):
            pass

        def request(self, *args, **kwargs):
            raise ConnectionRefusedError()

        def close(self):
            pass

    monkeypatch.setattr(ollama, "_LocalConnection", OfflineConnection)
