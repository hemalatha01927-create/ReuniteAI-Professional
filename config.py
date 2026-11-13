import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
APP_ENV = os.environ.get("APP_ENV", "development").lower()
IS_PRODUCTION = APP_ENV == "production"

# Do not silently generate a new secret on each production restart.
SECRET_KEY = os.environ.get("SECRET_KEY")
if IS_PRODUCTION and not SECRET_KEY:
    raise RuntimeError("SECRET_KEY must be set in the hosting provider environment.")

# Render/Neon commonly provide postgresql:// URLs. Use psycopg 3 explicitly.
DATABASE_URL = os.environ.get("DATABASE_URL", f"sqlite:///{BASE_DIR / 'reuniteai.sqlite3'}")
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql+psycopg://", 1)
elif DATABASE_URL.startswith("postgresql://"):
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+psycopg://", 1)


def env_bool(name, default):
    value = os.environ.get(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


class Config:
    SECRET_KEY = SECRET_KEY or os.urandom(32)
    SQLALCHEMY_DATABASE_URI = DATABASE_URL
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {"pool_pre_ping": True, "pool_recycle": 300}
    MAX_CONTENT_LENGTH = 5 * 1024 * 1024
    UPLOAD_FOLDER = os.environ.get("UPLOAD_FOLDER", str(BASE_DIR / "instance" / "private_uploads"))
    ALLOWED_IMAGE_EXTENSIONS = {"jpg", "jpeg", "png", "webp"}
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    REMEMBER_COOKIE_HTTPONLY = True
    WTF_CSRF_TIME_LIMIT = 3600
    RATELIMIT_STORAGE_URI = os.environ.get("RATELIMIT_STORAGE_URI", "memory://")
    SESSION_COOKIE_SECURE = env_bool("COOKIE_SECURE", IS_PRODUCTION)
    REMEMBER_COOKIE_SECURE = SESSION_COOKIE_SECURE
    PREFERRED_URL_SCHEME = "https" if SESSION_COOKIE_SECURE else "http"
    PUBLIC_REGISTRATION_ENABLED = env_bool("PUBLIC_REGISTRATION_ENABLED", not IS_PRODUCTION)
    PUBLIC_INTAKE_ENABLED = env_bool("PUBLIC_INTAKE_ENABLED", not IS_PRODUCTION)
    UPLOADS_ENABLED = env_bool("UPLOADS_ENABLED", not IS_PRODUCTION)
    IS_PRODUCTION = IS_PRODUCTION


class TestConfig(Config):
    TESTING = True
    WTF_CSRF_ENABLED = False
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    RATELIMIT_ENABLED = False
    PUBLIC_REGISTRATION_ENABLED = True
    PUBLIC_INTAKE_ENABLED = True
    UPLOADS_ENABLED = True
