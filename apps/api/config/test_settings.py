"""Disposable profile: no investigator database or fixture paths."""

import os
import tempfile
from pathlib import Path

os.environ["PROVE_PROFILE"] = "test"
from .settings import *

TEST_ROOT = Path(os.environ.get("PROVE_TEST_ROOT") or tempfile.mkdtemp(prefix="prove-test-"))
TEST_ROOT.mkdir(parents=True, exist_ok=True)
DATABASES = {
    "default": {"ENGINE": "django.db.backends.sqlite3", "NAME": TEST_ROOT / "test.sqlite3"}
}
EVIDENCE_ROOT = TEST_ROOT / "evidence"
OUTPUT_ROOT = TEST_ROOT / "output"
SYNTHETIC_ROOT = EVIDENCE_ROOT
for directory in (EVIDENCE_ROOT, OUTPUT_ROOT):
    directory.mkdir(parents=True, exist_ok=True)
CELERY_TASK_ALWAYS_EAGER = True
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False
SECURE_SSL_REDIRECT = False
ALLOWED_HOSTS = ["testserver", "127.0.0.1", "localhost"]
CSRF_TRUSTED_ORIGINS = ["http://127.0.0.1:5187"]
PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]
