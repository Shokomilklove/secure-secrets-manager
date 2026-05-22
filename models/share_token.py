import json
import os
import secrets
from datetime import datetime, timezone


def _tokens_path(data_dir: str) -> str:
    return os.path.join(data_dir, "share_tokens.json")


def _load_tokens(data_dir: str) -> list:
    path = _tokens_path(data_dir)
    if not os.path.exists(path):
        return []
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _save_tokens(data_dir: str, tokens: list) -> None:
    os.makedirs(data_dir, exist_ok=True)
    with open(_tokens_path(data_dir), "w", encoding="utf-8") as f:
        json.dump(tokens, f, indent=2)


def create_token(data_dir: str, secret_id: str, owner_id: str, expires_at: str) -> dict:
    tokens = _load_tokens(data_dir)
    token = {
        "token": secrets.token_urlsafe(32),
        "secret_id": secret_id,
        "owner_id": owner_id,
        "expires_at": expires_at,
        "used": False,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    tokens.append(token)
    _save_tokens(data_dir, tokens)
    return token


def get_token(data_dir: str, token_value: str) -> dict | None:
    tokens = _load_tokens(data_dir)
    return next((t for t in tokens if t["token"] == token_value), None)


def mark_token_used(data_dir: str, token_value: str) -> None:
    tokens = _load_tokens(data_dir)
    for t in tokens:
        if t["token"] == token_value:
            t["used"] = True
            break
    _save_tokens(data_dir, tokens)
