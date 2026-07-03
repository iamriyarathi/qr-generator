"""
Application configuration.

Reads sensible defaults and allows overrides via environment variables,
so the same codebase works locally and on Vercel's serverless runtime.
"""
import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

# Vercel's filesystem is read-only except for /tmp, so we point the
# instance/database/generated-file paths at /tmp when running there.
IS_VERCEL = bool(os.environ.get("VERCEL"))
INSTANCE_DIR = "/tmp/instance" if IS_VERCEL else os.path.join(BASE_DIR, "instance")
GENERATED_DIR = os.path.join(INSTANCE_DIR, "generated")

os.makedirs(INSTANCE_DIR, exist_ok=True)
os.makedirs(GENERATED_DIR, exist_ok=True)


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-key-change-in-production")
    DATABASE_PATH = os.path.join(INSTANCE_DIR, "qr_generator.db")
    GENERATED_DIR = GENERATED_DIR
    MAX_CONTENT_LENGTH = 5 * 1024 * 1024  # 5 MB upload limit (logo images)
    JSON_SORT_KEYS = False
    ALLOWED_LOGO_EXTENSIONS = {"png", "jpg", "jpeg"}
