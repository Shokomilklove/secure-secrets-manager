import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-change-in-production")
    JWT_SECRET = os.environ.get("JWT_SECRET", "jwt-secret-change-in-production")
    JWT_EXPIRY_HOURS = int(os.environ.get("JWT_EXPIRY_HOURS", "24"))
    FERNET_KEY = os.environ.get("FERNET_KEY", "")
    DATA_DIR = os.environ.get("DATA_DIR", os.path.join(os.path.dirname(__file__), "data"))
    SHARE_TOKEN_EXPIRY_MINUTES = int(os.environ.get("SHARE_TOKEN_EXPIRY_MINUTES", "60"))
    RATELIMIT_DEFAULT = os.environ.get("RATELIMIT_DEFAULT", "100 per hour")
    RATELIMIT_STORAGE_URI = os.environ.get("RATELIMIT_STORAGE_URI", "memory://")


class DevelopmentConfig(Config):
    DEBUG = True


class ProductionConfig(Config):
    DEBUG = False


class TestingConfig(Config):
    TESTING = True
    DATA_DIR = os.path.join(os.path.dirname(__file__), "test_data")


config_map = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
    "testing": TestingConfig,
}

active_config = config_map.get(os.environ.get("FLASK_ENV", "development"), DevelopmentConfig)
