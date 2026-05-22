import os
import json
from datetime import datetime, timedelta, timezone
from functools import wraps

import jwt
from flask import current_app, g, jsonify, request


def generate_token(user_id: str, username: str, jwt_secret: str, expiry_hours: int) -> str:
    payload = {
        "sub": user_id,
        "username": username,
        "exp": datetime.now(timezone.utc) + timedelta(hours=expiry_hours),
        "iat": datetime.now(timezone.utc),
    }
    return jwt.encode(payload, jwt_secret, algorithm="HS256")


def decode_token(token: str, jwt_secret: str) -> dict:
    return jwt.decode(token, jwt_secret, algorithms=["HS256"])


def require_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            return jsonify({"error": "Missing or invalid Authorization header"}), 401
        token = auth_header[7:]
        try:
            payload = decode_token(token, current_app.config["JWT_SECRET"])
        except jwt.ExpiredSignatureError:
            return jsonify({"error": "Token expired"}), 401
        except jwt.InvalidTokenError:
            return jsonify({"error": "Invalid token"}), 401
        g.user_id = payload["sub"]
        g.username = payload["username"]
        return f(*args, **kwargs)
    return decorated
