from datetime import datetime, timedelta, timezone

from flask import Blueprint, current_app, g, jsonify, request

from models import secret as secret_model
from models import share_token as token_model
from utils.audit import log_event
from utils.auth import require_auth
from utils.encryption import decrypt, encrypt

secrets_bp = Blueprint("secrets", __name__)


@secrets_bp.route("/secrets", methods=["POST"])
@require_auth
def create_secret():
    data = request.get_json(silent=True) or {}
    name = data.get("name", "").strip()
    value = data.get("value", "")
    description = data.get("description", "")
    tags = data.get("tags", [])

    if not name:
        return jsonify({"error": "name is required"}), 400
    if not value:
        return jsonify({"error": "value is required"}), 400
    if not isinstance(tags, list):
        return jsonify({"error": "tags must be a list"}), 400

    data_dir = current_app.config["DATA_DIR"]
    fernet_key = current_app.config["FERNET_KEY"]
    encrypted_value = encrypt(value, fernet_key)

    secret = secret_model.create_secret(
        data_dir, g.user_id, name, encrypted_value, description, tags
    )
    log_event(data_dir, "secret_created", g.user_id, {"secret_id": secret["id"], "name": name})
    return jsonify({"message": "Secret stored", "secret": secret}), 201


@secrets_bp.route("/secrets", methods=["GET"])
@require_auth
def list_secrets():
    data_dir = current_app.config["DATA_DIR"]
    secrets = secret_model.list_secrets(data_dir, g.user_id)
    log_event(data_dir, "secrets_listed", g.user_id)
    return jsonify({"secrets": secrets}), 200


@secrets_bp.route("/secrets/<secret_id>", methods=["GET"])
@require_auth
def get_secret(secret_id):
    data_dir = current_app.config["DATA_DIR"]
    secret = secret_model.get_secret(data_dir, secret_id)

    if secret is None or secret["owner_id"] != g.user_id:
        return jsonify({"error": "Secret not found"}), 404

    fernet_key = current_app.config["FERNET_KEY"]
    decrypted_value = decrypt(secret["encrypted_value"], fernet_key)

    log_event(data_dir, "secret_accessed", g.user_id, {"secret_id": secret_id})
    return jsonify({
        "id": secret["id"],
        "name": secret["name"],
        "value": decrypted_value,
        "description": secret["description"],
        "tags": secret["tags"],
        "created_at": secret["created_at"],
        "updated_at": secret["updated_at"],
    }), 200


@secrets_bp.route("/secrets/<secret_id>", methods=["PUT"])
@require_auth
def update_secret(secret_id):
    data_dir = current_app.config["DATA_DIR"]
    secret = secret_model.get_secret(data_dir, secret_id)

    if secret is None or secret["owner_id"] != g.user_id:
        return jsonify({"error": "Secret not found"}), 404

    data = request.get_json(silent=True) or {}
    name = data.get("name")
    description = data.get("description")
    tags = data.get("tags")

    if tags is not None and not isinstance(tags, list):
        return jsonify({"error": "tags must be a list"}), 400

    updated = secret_model.update_secret(data_dir, secret_id, name, description, tags)
    log_event(data_dir, "secret_updated", g.user_id, {"secret_id": secret_id})
    return jsonify({"message": "Secret updated", "secret": updated}), 200


@secrets_bp.route("/secrets/<secret_id>", methods=["DELETE"])
@require_auth
def delete_secret(secret_id):
    data_dir = current_app.config["DATA_DIR"]
    secret = secret_model.get_secret(data_dir, secret_id)

    if secret is None or secret["owner_id"] != g.user_id:
        return jsonify({"error": "Secret not found"}), 404

    secret_model.delete_secret(data_dir, secret_id)
    log_event(data_dir, "secret_deleted", g.user_id, {"secret_id": secret_id})
    return jsonify({"message": "Secret deleted"}), 200


@secrets_bp.route("/secrets/<secret_id>/share", methods=["POST"])
@require_auth
def share_secret(secret_id):
    data_dir = current_app.config["DATA_DIR"]
    secret = secret_model.get_secret(data_dir, secret_id)

    if secret is None or secret["owner_id"] != g.user_id:
        return jsonify({"error": "Secret not found"}), 404

    expiry_minutes = current_app.config["SHARE_TOKEN_EXPIRY_MINUTES"]
    expires_at = (datetime.now(timezone.utc) + timedelta(minutes=expiry_minutes)).isoformat()

    token = token_model.create_token(data_dir, secret_id, g.user_id, expires_at)
    log_event(data_dir, "share_token_created", g.user_id, {
        "secret_id": secret_id, "expires_at": expires_at
    })
    return jsonify({
        "token": token["token"],
        "expires_at": token["expires_at"],
    }), 201
