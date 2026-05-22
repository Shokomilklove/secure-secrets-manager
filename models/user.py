import json
import os
import uuid
from datetime import datetime, timezone

from werkzeug.security import check_password_hash, generate_password_hash


def _users_path(data_dir: str) -> str:
    return os.path.join(data_dir, "users.json")


def _load_users(data_dir: str) -> list:
    path = _users_path(data_dir)
    if not os.path.exists(path):
        return []
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _save_users(data_dir: str, users: list) -> None:
    os.makedirs(data_dir, exist_ok=True)
    path = _users_path(data_dir)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(users, f, indent=2)


def create_user(data_dir: str, username: str, password: str) -> dict:
    users = _load_users(data_dir)
    if any(u["username"] == username for u in users):
        raise ValueError("Username already exists")
    user = {
        "id": str(uuid.uuid4()),
        "username": username,
        "password_hash": generate_password_hash(password),
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    users.append(user)
    _save_users(data_dir, users)
    return _public(user)


def get_user_by_username(data_dir: str, username: str) -> dict | None:
    users = _load_users(data_dir)
    return next((u for u in users if u["username"] == username), None)


def get_user_by_id(data_dir: str, user_id: str) -> dict | None:
    users = _load_users(data_dir)
    return next((u for u in users if u["id"] == user_id), None)


def verify_password(user: dict, password: str) -> bool:
    return check_password_hash(user["password_hash"], password)


def _public(user: dict) -> dict:
    return {"id": user["id"], "username": user["username"], "created_at": user["created_at"]}
