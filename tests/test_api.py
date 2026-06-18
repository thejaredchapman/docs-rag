import pytest

import app as app_module


@pytest.fixture
def client(built_index, fake_chat):
    app_module.app.testing = True
    return app_module.app.test_client()


def test_health(client):
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.get_json()["status"] == "ok"


def test_ask_endpoint(client):
    response = client.post("/api/ask", json={"question": "What is this about?"})
    assert response.status_code == 200
    data = response.get_json()
    assert "answer" in data
    assert data["sources"] == ["sample.md"]


def test_ask_endpoint_missing_question(client):
    response = client.post("/api/ask", json={})
    assert response.status_code == 400


def test_sources_endpoint(client):
    response = client.get("/api/sources")
    assert response.status_code == 200
    assert response.get_json()["sources"] == ["sample.md"]


def test_stats_endpoint(client):
    response = client.get("/api/stats")
    assert response.status_code == 200
    data = response.get_json()
    assert "total_chunks" in data
    assert "cache" in data


def test_security_headers_present(client):
    response = client.get("/api/health")
    assert response.headers["X-Frame-Options"] == "DENY"
    assert response.headers["X-Content-Type-Options"] == "nosniff"


def test_index_missing_returns_503(client, temp_index_dir):
    # built_index already ran for this client's fixtures, but simulate a
    # fresh app with no index by pointing query at an empty temp dir again.
    import config

    config.FAISS_INDEX_PATH.unlink()
    import query

    query._index = None
    response = client.post("/api/ask", json={"question": "anything"})
    assert response.status_code == 503
    assert "sk-" not in response.get_json()["error"]
