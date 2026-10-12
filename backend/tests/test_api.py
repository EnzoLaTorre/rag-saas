import uuid

import pytest


def _register(client, tenant="Acme"):
    email = f"{uuid.uuid4().hex}@example.com"
    res = client.post(
        "/api/auth/register",
        json={
            "tenant_name": tenant,
            "email": email,
            "full_name": "Test User",
            "password": "secret123",
        },
    )
    assert res.status_code == 200, res.text
    return res.json()["access_token"]


def _auth(token):
    return {"Authorization": f"Bearer {token}"}


@pytest.mark.integration
def test_register_login_me(client):
    token = _register(client)

    me = client.get("/api/auth/me", headers=_auth(token))
    assert me.status_code == 200
    assert me.json()["role"] == "admin"

    login = client.post(
        "/api/auth/login",
        data={"username": "demo@example.com", "password": "x"},
    )
    assert login.status_code in (401, 400)


@pytest.mark.integration
def test_documentos_aislados_por_tenant(client):
    token_a = _register(client, "A")
    token_b = _register(client, "B")

    files = {"file": ("nota.txt", b"El gato duerme en el sofa.", "text/plain")}
    up = client.post("/api/documents", files=files, headers=_auth(token_a))
    assert up.status_code == 200, up.text

    docs_a = client.get("/api/documents", headers=_auth(token_a)).json()
    docs_b = client.get("/api/documents", headers=_auth(token_b)).json()
    assert len(docs_a) == 1
    assert docs_a[0]["status"] == "ready"
    assert docs_a[0]["chunk_count"] >= 1
    assert docs_b == []


@pytest.mark.integration
def test_chat_query_stream(client):
    token = _register(client)
    files = {"file": ("nota.txt", b"El gato duerme en el sofa.", "text/plain")}
    client.post("/api/documents", files=files, headers=_auth(token))

    res = client.post(
        "/api/chat/query",
        json={"question": "¿Dónde duerme el gato?"},
        headers=_auth(token),
    )
    assert res.status_code == 200
    assert '"type": "sources"' in res.text
    assert '"type": "done"' in res.text

    history = client.get("/api/chat/history", headers=_auth(token)).json()
    assert len(history) == 1
    assert history[0]["question"] == "¿Dónde duerme el gato?"


@pytest.mark.integration
def test_borrar_documento(client):
    token = _register(client)
    files = {"file": ("nota.txt", b"contenido", "text/plain")}
    doc = client.post("/api/documents", files=files, headers=_auth(token)).json()

    assert client.delete(f"/api/documents/{doc['id']}", headers=_auth(token)).status_code == 200
    assert client.get("/api/documents", headers=_auth(token)).json() == []
