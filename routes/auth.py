from flask import Blueprint, current_app, jsonify, request

from models import user as user_model
from utils.audit import log_event
from utils.auth import generate_token

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/register", methods=["POST"])
def register():
    data = request.get_json(silent=True) or {}
    username = data.get("username", "").strip()
    password = data.get("password", "")

    if not username or not password:
        return jsonify({"error": "username and password are required"}), 400
    if len(username) < 3 or len(username) > 64:
        return jsonify({"error": "username must be 3-64 characters"}), 400
    if len(password) < 8:
        return jsonify({"error": "password must be at least 8 characters"}), 400

    data_dir = current_app.config["DATA_DIR"]
    try:
        new_user = user_model.create_user(data_dir, username, password)
    except ValueError as e:
        return jsonify({"error": str(e)}), 409

    log_event(data_dir, "user_registered", new_user["id"], {"username": username})
    return jsonify({"message": "User registered", "user": new_user}), 201


@auth_bp.route("/login", methods=["POST"])
def login():
    data = request.get_json(silent=True) or {}
    username = data.get("username", "").strip()
    password = data.get("password", "")

    if not username or not password:
        return jsonify({"error": "username and password are required"}), 400

    data_dir = current_app.config["DATA_DIR"]
    db_user = user_model.get_user_by_username(data_dir, username)
    if db_user is None or not user_model.verify_password(db_user, password):
        log_event(data_dir, "login_failed", None, {"username": username})
        return jsonify({"error": "Invalid credentials"}), 401

    token = generate_token(
        db_user["id"],
        db_user["username"],
        current_app.config["JWT_SECRET"],
        current_app.config["JWT_EXPIRY_HOURS"],
    )
    log_event(data_dir, "login_success", db_user["id"], {"username": username})
    return jsonify({"token": token}), 200
