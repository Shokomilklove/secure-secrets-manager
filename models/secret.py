import json
import os
import uuid
from datetime import datetime, timezone


def _secrets_dir(data_dir: str) -> str:
    return os.path.join(data_dir, "secrets")


def _secret_path(data_dir: str, secret_id: str) -> str:
    return os.path.join(_secrets_dir(data_dir), f"{secret_id}.json")


def create_secret(data_dir: str, owner_id: str, name: str, encrypted_value: str,
                  description: str = "", tags: list | None = None) -> dict:
    secret = {
        "id": str(uuid.uuid4()),
        "owner_id": owner_id,
        "name": name,
        "encrypted_value": encrypted_value,
        "description": description,
        "tags": tags or [],
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }
    os.makedirs(_secrets_dir(data_dir), exist_ok=True)
    with open(_secret_path(data_dir, secret["id"]), "w", encoding="utf-8") as f:
        json.dump(secret, f, indent=2)
    return _public(secret)


def get_secret(data_dir: str, secret_id: str) -> dict | None:
    path = _secret_path(data_dir, secret_id)
    if not os.path.exists(path):
        return None
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def update_secret(data_dir: str, secret_id: str, name: str | None = None,
                  description: str | None = None, tags: list | None = None) -> dict | None:
    secret = get_secret(data_dir, secret_id)
    if secret is None:
        return None
    if name is not None:
        secret["name"] = name
    if description is not None:
        secret["description"] = description
    if tags is not None:
        secret["tags"] = tags
    secret["updated_at"] = datetime.now(timezone.utc).isoformat()
    with open(_secret_path(data_dir, secret_id), "w", encoding="utf-8") as f:
        json.dump(secret, f, indent=2)
    return _public(secret)


def delete_secret(data_dir: str, secret_id: str) -> bool:
    path = _secret_path(data_dir, secret_id)
    if not os.path.exists(path):
        return False
    os.remove(path)
    return True


def list_secrets(data_dir: str, owner_id: str) -> list:
    secrets_dir = _secrets_dir(data_dir)
    if not os.path.exists(secrets_dir):
        return []
    result = []
    for filename in os.listdir(secrets_dir):
        if not filename.endswith(".json"):
            continue
        path = os.path.join(secrets_dir, filename)
        with open(path, "r", encoding="utf-8") as f:
            secret = json.load(f)
        if secret["owner_id"] == owner_id:
            result.append(_public(secret))
    return result


def _public(secret: dict) -> dict:
    return {
        "id": secret["id"],
        "owner_id": secret["owner_id"],
        "name": secret["name"],
        "description": secret["description"],
        "tags": secret["tags"],
        "created_at": secret["created_at"],
        "updated_at": secret["updated_at"],
    }
