import io
import json
import socket

import pytest
from fastapi.testclient import TestClient
from orbit_engine import ollama, providers
from orbit_engine.app import create_app


class Response:
    status = 200

    def __init__(self, body=b'{"models": []}', status=200, length=None):
        self.body = io.BytesIO(body)
        self.status = status
        self.length = length

    def close(self):
        pass

    def getheader(self, name):
        return self.length

    def read1(self, size):
        return self.body.read(size)


@pytest.fixture
def server(monkeypatch):
    calls = []

    class Connection:
        response = Response()
        error = None
        sock = None
        closed = False

        def __init__(self, *args, **kwargs):
            calls.append((args, kwargs))

        def request(self, *args, **kwargs):
            calls.append((args, kwargs))
            if self.error:
                raise self.error

        def getresponse(self):
            return self.response

        def close(self):
            type(self).closed = True

    monkeypatch.setattr(ollama, "_LocalConnection", Connection)
    return Connection, calls


@pytest.mark.parametrize("endpoint", ["http://localhost:11434", "http://127.0.0.2:11434",
    "http://127.0.0.1:11434@evil.example", "https://ollama.com", "http://[::1]:11434",
    "http://127.0.0.1:11434/", "http://user:pass@127.0.0.1:11434"])
def test_fixed_endpoint_only(server, endpoint):
    _, calls = server
    assert ollama.discover(endpoint)["status"] == "invalid_endpoint"
    assert calls == []


def test_installed_metadata_is_sanitized_and_not_tool_readiness(server, monkeypatch):
    connection, calls = server
    monkeypatch.setenv("OLLAMA_HOST", "https://evil.example")
    monkeypatch.setenv("HTTP_PROXY", "https://evil.example")
    connection.response = Response(json.dumps({"models": [
        {"name": "gemma3:4b", "model": "gemma3:4b", "size": 123,
         "digest": "abc123", "modified_at": "2026-10-31T10:00:00Z",
         "secret": "must disappear", "details": {"family": "gemma3",
         "families": ["gemma3"], "parameter_size": "4B", "format": "gguf",
         "quantization_level": "Q4_K_M", "password": "secret"}},
        {"name": "qwen3:8b", "digest": "bad\nheader", "size": True}]}).encode())
    result = ollama.discover()
    assert result["status"] == "available"
    assert result["reachable"] is True
    assert result["execution_ready"] is False
    assert result["authentication"] == "unknown"
    assert result["models"][0]["size_bytes"] == 123
    assert result["models"][0]["details"]["family"] == "gemma3"
    assert result["models"][1] == {"name": "qwen3:8b", "capabilities": {"tools": "unknown"}}
    assert "secret" not in json.dumps(result)
    assert calls[0][0] == ("127.0.0.1", 11434)
    assert calls[1] == (("GET", "/api/tags"), {"headers": {"Accept": "application/json"}})
    assert connection.closed


@pytest.mark.parametrize("error,status", [(ConnectionRefusedError(), "offline"),
    (socket.timeout(), "timeout"), (OSError("private failure"), "offline")])
def test_unavailable(server, error, status):
    connection, _ = server
    connection.error = error
    result = ollama.discover()
    assert result["status"] == status
    assert result["models"] == []
    assert connection.closed
    assert "private failure" not in json.dumps(result)


@pytest.mark.parametrize("status,expected", [(301, "redirect_rejected"),
    (307, "redirect_rejected"), (401, "http_error"), (500, "http_error")])
def test_no_redirect_or_auth_retry(server, status, expected):
    connection, calls = server
    connection.response = Response(status=status)
    assert ollama.discover()["status"] == expected
    assert len(calls) == 2


@pytest.mark.parametrize("body", [b'bad', b'null', b'{"models": {}}', b'{"models": [1]}',
    b'{"models": [{"name": "<script>"}]}', b'\xff', b'x' * (ollama.MAX_BYTES + 1),
    json.dumps({"models": [{"name": "qwen"}] * (ollama.MAX_MODELS + 1)}).encode()])
def test_malformed_and_oversized(server, body):
    connection, _ = server
    connection.response = Response(body)
    assert ollama.discover()["status"] == "malformed"
    assert connection.closed


@pytest.mark.parametrize("length", [str(ollama.MAX_BYTES + 1), "invalid"])
def test_reject_size_header_before_read(server, length):
    connection, _ = server
    connection.response = Response(length=length)
    assert ollama.discover()["status"] == "malformed"
    assert connection.response.body.tell() == 0


def test_deadline_includes_body(server, monkeypatch):
    times = iter([0, 1])
    monkeypatch.setattr(ollama.time, "monotonic", lambda: next(times))
    assert ollama.discover()["status"] == "timeout"


def test_socket_deadline_prevents_slow_header_reads(monkeypatch):
    with ollama._DeadlineSocket() as sock:
        sock.deadline = 0
        monkeypatch.setattr(ollama.time, "monotonic", lambda: 1)
        with pytest.raises(TimeoutError):
            sock.recv_into(bytearray(1))


def test_provider_api_preserves_cloud_invariants(server, tmp_path):
    token = "test-session-token-at-least-32-characters"
    with TestClient(create_app(tmp_path / "state.db", token)) as client:
        response = client.get("/v1/providers", headers={"Authorization": f"Bearer {token}"})
    declarations = response.json()
    assert isinstance(declarations, list)
    assert [p["id"] for p in declarations] == list(providers.PROVIDERS)
    for provider in declarations:
        assert provider["execution_enabled"] is False
        assert provider["paid_api_fallback"] is False
        assert provider["energy"]["remaining_percent"] is None
        assert provider["energy"]["status"] == "unknown"
    for provider in declarations[:-1]:
        assert provider["auth"] == "unknown"
        assert provider["energy"]["kind"] == "shared-quota"
        assert "discovery" not in provider
    assert declarations[-1]["energy"]["kind"] == "compute"
    assert declarations[-1]["auth"] == "local"
    assert declarations[-1]["discovery"]["status"] == "empty"


def test_truncated_body_is_malformed(server):
    connection, _ = server
    connection.response = Response(b'{"models": []}', length="99")
    assert ollama.discover()["status"] == "malformed"
