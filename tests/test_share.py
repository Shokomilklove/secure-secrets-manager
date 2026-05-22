def _create_and_share(client, auth_headers):
    create = client.post("/secrets", json={"name": "SHARED", "value": "shared-value"}, headers=auth_headers)
    secret_id = create.get_json()["secret"]["id"]
    share = client.post(f"/secrets/{secret_id}/share", headers=auth_headers)
    assert share.status_code == 201
    return share.get_json()["token"]


def test_share_and_access(client, auth_headers):
    token = _create_and_share(client, auth_headers)
    r = client.get(f"/share/{token}")
    assert r.status_code == 200
    assert r.get_json()["value"] == "shared-value"


def test_token_one_time_use(client, auth_headers):
    token = _create_and_share(client, auth_headers)
    client.get(f"/share/{token}")
    r = client.get(f"/share/{token}")
    assert r.status_code == 410


def test_invalid_token(client):
    r = client.get("/share/nonexistent-token")
    assert r.status_code == 404


def test_share_nonexistent_secret(client, auth_headers):
    r = client.post("/secrets/00000000-0000-0000-0000-000000000000/share", headers=auth_headers)
    assert r.status_code == 404
