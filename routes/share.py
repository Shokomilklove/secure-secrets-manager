from datetime import datetime, timezone

from flask import Blueprint, current_app, jsonify, request

from models import secret as secret_model
from models import share_token as token_model
from utils.audit import log_event
from utils.encryption import decrypt

share_bp = Blueprint("share", __name__)


@share_bp.route("/share/<token_value>", methods=["GET"])
def access_shared_secret(token_value):
    data_dir = current_app.config["DATA_DIR"]
    token = token_model.get_token(data_dir, token_value)

    if token is None:
        return jsonify({"error": "Invalid or expired token"}), 404

    if token["used"]:
        log_event(data_dir, "share_token_reused_attempt", None, {"token": token_value[:8] + "..."})
        return jsonify({"error": "Token has already been used"}), 410

    expires_at = datetime.fromisoformat(token["expires_at"])
    if datetime.now(timezone.utc) > expires_at:
        log_event(data_dir, "share_token_expired_attempt", None, {"token": token_value[:8] + "..."})
        return jsonify({"error": "Token has expired"}), 410

    secret = secret_model.get_secret(data_dir, token["secret_id"])
    if secret is None:
        return jsonify({"error": "Secret no longer exists"}), 404

    fernet_key = current_app.config["FERNET_KEY"]
    decrypted_value = decrypt(secret["encrypted_value"], fernet_key)

    token_model.mark_token_used(data_dir, token_value)
    log_event(data_dir, "share_token_accessed", token["owner_id"], {
        "secret_id": token["secret_id"],
    })

    return jsonify({
        "name": secret["name"],
        "value": decrypted_value,
        "description": secret["description"],
    }), 200
