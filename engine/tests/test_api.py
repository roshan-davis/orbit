from pathlib import Path
import pytest
from fastapi.testclient import TestClient
from orbit_engine.app import create_app

TOKEN = "test-session-token-at-least-32-characters"
HEADERS = {"Authorization": f"Bearer {TOKEN}"}
PROFILE = {"name": "Alex", "role": "engineer", "seniority": "principal",
           "expertise": ["architecture"], "provider": "ollama", "model": "qwen"}

def test_auth_required_and_no_data_leaked(tmp_path):
    with TestClient(create_app(tmp_path / "test.db", TOKEN)) as client:
        assert client.get("/health").status_code == 200
        for endpoint in ("/v1/agents", "/v1/providers"):
            assert client.get(endpoint).status_code == 401
            assert client.get(endpoint, headers={"Authorization": "Bearer wrong"}).status_code == 401
        assert client.post("/v1/agents", json=PROFILE).status_code == 401

def test_profile_survives_engine_restart(tmp_path):
    path = tmp_path / "state.db"
    with TestClient(create_app(path, TOKEN)) as client:
        response = client.post("/v1/agents", json=PROFILE, headers=HEADERS)
        assert response.status_code == 201
        saved = response.json()
        assert saved["id"]
    with TestClient(create_app(path, TOKEN)) as client:
        assert client.get("/v1/agents", headers=HEADERS).json() == [saved]

def test_reject_unknown_provider_and_empty_identity(tmp_path):
    with TestClient(create_app(tmp_path / "state.db", TOKEN)) as client:
        for invalid in ({**PROFILE, "provider": "paid-api"}, {**PROFILE, "name": ""}):
            assert client.post("/v1/agents", json=invalid, headers=HEADERS).status_code == 422

def test_provider_declarations_do_not_invent_readiness_or_quota(tmp_path):
    with TestClient(create_app(tmp_path / "state.db", TOKEN)) as client:
        providers = client.get("/v1/providers", headers=HEADERS).json()
        assert len(providers) == 4
        for provider in providers:
            assert provider["execution_enabled"] is False
            assert provider["paid_api_fallback"] is False
            assert provider["energy"]["remaining_percent"] is None
        assert providers[-1]["energy"]["kind"] == "compute"

def test_engine_rejects_missing_token(tmp_path):
    with pytest.raises(RuntimeError, match="ORBIT_TOKEN"):
        with TestClient(create_app(tmp_path / "state.db", "")):
            pass

def test_unknown_schema_is_preserved(tmp_path):
    import sqlite3
    path = tmp_path / "future.db"
    with sqlite3.connect(path) as db:
        db.execute("PRAGMA user_version=99")
    with pytest.raises(RuntimeError, match="schema"):
        with TestClient(create_app(path, TOKEN)):
            pass
    with sqlite3.connect(path) as db:
        assert db.execute("PRAGMA user_version").fetchone()[0] == 99

def test_cors_does_not_allow_arbitrary_websites(tmp_path):
    with TestClient(create_app(tmp_path / "test.db", TOKEN)) as client:
        response = client.options("/v1/agents", headers={
            "Origin": "https://untrusted.example", "Access-Control-Request-Method": "GET"})
        assert "access-control-allow-origin" not in response.headers


def test_edit_preserves_identity_and_all_fields_across_restart(tmp_path):
    import sqlite3
    path = tmp_path / "state.db"
    profile = {**PROFILE, "skills": ["review@v1", "design@sha256:abc"],
               "instructions": "Keep all instructions.\nIncluding newlines.", "tools": ["read-files"]}
    with TestClient(create_app(path, TOKEN)) as client:
        saved = client.post('/v1/agents', json=profile, headers=HEADERS).json()
        updated = {**profile, "provider": "codex-cli", "model": "configured-model", "name": "Renamed"}
        response = client.put(f'/v1/agents/{saved["id"]}', json=updated, headers=HEADERS)
        assert response.status_code == 200
        expected = {**updated, "id": saved['id']}
        assert response.json() == expected
        assert client.get(f'/v1/agents/{saved["id"]}', headers=HEADERS).json() == expected
    with TestClient(create_app(path, TOKEN)) as client:
        assert client.get('/v1/agents', headers=HEADERS).json() == [expected]
    with sqlite3.connect(path) as db:
        assert db.execute('PRAGMA user_version').fetchone()[0] == 1


def test_retrieve_update_boundaries_and_defaults(tmp_path):
    with TestClient(create_app(tmp_path / 'state.db', TOKEN)) as client:
        for headers in ({}, {"Authorization": "Bearer wrong"}):
            assert client.get('/v1/agents/missing', headers=headers).status_code == 401
            assert client.put('/v1/agents/missing', json=PROFILE, headers=headers).status_code == 401
        assert client.get('/v1/agents/missing', headers=HEADERS).status_code == 404
        assert client.put('/v1/agents/missing', json=PROFILE, headers=HEADERS).status_code == 404
        saved = client.post('/v1/agents', json=PROFILE, headers=HEADERS).json()
        assert saved['tools'] == []
        route = f'/v1/agents/{saved["id"]}'
        for field in ('name', 'role', 'seniority', 'model'):
            invalid = {**PROFILE, field: '  \t '}
            assert client.post('/v1/agents', json=invalid, headers=HEADERS).status_code == 422
            assert client.put(route, json=invalid, headers=HEADERS).status_code == 422
        for invalid in ({**PROFILE, 'provider': 'paid-api'}, {'name': 'partial'}, {**PROFILE, 'skills': [123]}):
            assert client.put(route, json=invalid, headers=HEADERS).status_code == 422
        assert client.get(route, headers=HEADERS).json() == saved
        assert client.get('/v1/agents', headers=HEADERS).json() == [saved]


def test_cors_permits_only_required_methods(tmp_path):
    with TestClient(create_app(tmp_path / 'state.db', TOKEN)) as client:
        for method in ('GET', 'POST', 'PUT', 'DELETE', 'PATCH'):
            response = client.options('/v1/agents/example', headers={
                'Origin': 'http://localhost:1420', 'Access-Control-Request-Method': method,
                'Access-Control-Request-Headers': 'authorization,content-type'})
            assert response.status_code == (200 if method in ('GET', 'POST', 'PUT') else 400)
