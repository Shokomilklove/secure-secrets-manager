def test_register_success(client):
    r = client.post("/register", json={"username": "alice", "password": "securepass"})
    assert r.status_code == 201
    assert r.get_json()["user"]["username"] == "alice"


def test_register_duplicate(client):
    client.post("/register", json={"username": "bob", "password": "securepass"})
    r = client.post("/register", json={"username": "bob", "password": "securepass"})
    assert r.status_code == 409


def test_register_short_password(client):
    r = client.post("/register", json={"username": "charlie", "password": "short"})
    assert r.status_code == 400


def test_login_success(client):
    client.post("/register", json={"username": "dave", "password": "mypassword"})
    r = client.post("/login", json={"username": "dave", "password": "mypassword"})
    assert r.status_code == 200
    assert "token" in r.get_json()


def test_login_wrong_password(client):
    client.post("/register", json={"username": "eve", "password": "mypassword"})
    r = client.post("/login", json={"username": "eve", "password": "wrongpass"})
    assert r.status_code == 401


def test_login_unknown_user(client):
    r = client.post("/login", json={"username": "nobody", "password": "pass"})
    assert r.status_code == 401
