import os
import shutil
import pytest

from app import create_app
from config import TestingConfig
from utils.encryption import generate_key


class _TestConfig(TestingConfig):
    JWT_SECRET = "test-jwt-secret"
    FERNET_KEY = generate_key()
    RATELIMIT_ENABLED = False
    RATELIMIT_DEFAULT = "10000 per hour"


@pytest.fixture()
def app(tmp_path):
    _TestConfig.DATA_DIR = str(tmp_path)
    application = create_app(_TestConfig)
    yield application


@pytest.fixture()
def client(app):
    return app.test_client()


@pytest.fixture()
def auth_headers(client):
    client.post("/register", json={"username": "testuser", "password": "password123"})
    resp = client.post("/login", json={"username": "testuser", "password": "password123"})
    token = resp.get_json()["token"]
    return {"Authorization": f"Bearer {token}"}
