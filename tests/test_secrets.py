def test_create_secret(client, auth_headers):
    r = client.post("/secrets", json={"name": "API_KEY", "value": "super-secret"}, headers=auth_headers)
    assert r.status_code == 201
    data = r.get_json()
    assert data["secret"]["name"] == "API_KEY"
    assert "value" not in data["secret"]


def test_get_secret(client, auth_headers):
    create = client.post("/secrets", json={"name": "DB_PASS", "value": "hunter2"}, headers=auth_headers)
    secret_id = create.get_json()["secret"]["id"]
    r = client.get(f"/secrets/{secret_id}", headers=auth_headers)
    assert r.status_code == 200
    assert r.get_json()["value"] == "hunter2"


def test_list_secrets(client, auth_headers):
    client.post("/secrets", json={"name": "S1", "value": "v1"}, headers=auth_headers)
    client.post("/secrets", json={"name": "S2", "value": "v2"}, headers=auth_headers)
    r = client.get("/secrets", headers=auth_headers)
    assert r.status_code == 200
    assert len(r.get_json()["secrets"]) == 2


def test_update_secret(client, auth_headers):
    create = client.post("/secrets", json={"name": "OLD", "value": "val"}, headers=auth_headers)
    secret_id = create.get_json()["secret"]["id"]
    r = client.put(f"/secrets/{secret_id}", json={"name": "NEW", "description": "updated"}, headers=auth_headers)
    assert r.status_code == 200
    assert r.get_json()["secret"]["name"] == "NEW"


def test_delete_secret(client, auth_headers):
    create = client.post("/secrets", json={"name": "TEMP", "value": "val"}, headers=auth_headers)
    secret_id = create.get_json()["secret"]["id"]
    r = client.delete(f"/secrets/{secret_id}", headers=auth_headers)
    assert r.status_code == 200
    r2 = client.get(f"/secrets/{secret_id}", headers=auth_headers)
    assert r2.status_code == 404


def test_cannot_access_other_users_secret(client, app):
    client.post("/register", json={"username": "user1", "password": "password1"})
    client.post("/register", json={"username": "user2", "password": "password2"})
    r1 = client.post("/login", json={"username": "user1", "password": "password1"})
    r2 = client.post("/login", json={"username": "user2", "password": "password2"})
    h1 = {"Authorization": f"Bearer {r1.get_json()['token']}"}
    h2 = {"Authorization": f"Bearer {r2.get_json()['token']}"}

    create = client.post("/secrets", json={"name": "MINE", "value": "private"}, headers=h1)
    secret_id = create.get_json()["secret"]["id"]

    r = client.get(f"/secrets/{secret_id}", headers=h2)
    assert r.status_code == 404


def test_unauthenticated_access(client):
    r = client.get("/secrets")
    assert r.status_code == 401
