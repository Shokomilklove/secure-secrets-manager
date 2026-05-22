import os

from flask import Flask, jsonify
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

from config import active_config
from routes.auth import auth_bp
from routes.secrets import secrets_bp
from routes.share import share_bp
from utils.encryption import generate_key


def create_app(config=None):
    app = Flask(__name__)
    app.config.from_object(config or active_config)

    _ensure_fernet_key(app)

    limiter = Limiter(
        key_func=get_remote_address,
        app=app,
        default_limits=[app.config.get("RATELIMIT_DEFAULT", "100 per hour")],
        storage_uri=app.config.get("RATELIMIT_STORAGE_URI", "memory://"),
    )

    app.register_blueprint(auth_bp)
    app.register_blueprint(secrets_bp)
    app.register_blueprint(share_bp)

    # Apply tighter limits to auth endpoints
    limiter.limit("10 per minute")(auth_bp)

    @app.errorhandler(404)
    def not_found(_):
        return jsonify({"error": "Not found"}), 404

    @app.errorhandler(405)
    def method_not_allowed(_):
        return jsonify({"error": "Method not allowed"}), 405

    @app.errorhandler(429)
    def rate_limit_exceeded(_):
        return jsonify({"error": "Rate limit exceeded"}), 429

    return app


def _ensure_fernet_key(app: Flask) -> None:
    if not app.config.get("FERNET_KEY"):
        key = generate_key()
        app.config["FERNET_KEY"] = key
        env_path = os.path.join(os.path.dirname(__file__), ".env")
        with open(env_path, "a", encoding="utf-8") as f:
            f.write(f"\nFERNET_KEY={key}\n")
        app.logger.warning(
            "No FERNET_KEY set — generated a new key and appended it to .env. "
            "Back it up; losing it means losing all encrypted secrets."
        )


if __name__ == "__main__":
    application = create_app()
    application.run(host="0.0.0.0", port=5000, debug=False)
