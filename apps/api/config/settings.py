import os
from pathlib import Path
from urllib.parse import urlparse

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
PROFILE = os.getenv("PROVE_PROFILE", "development")
if PROFILE not in {"development", "test", "team"}:
    raise ValueError("PROVE_PROFILE must be development, test or team")
if PROFILE == "development":
    load_dotenv(BASE_DIR.parent.parent / ".env")
SECRET_KEY = os.getenv("SECRET_KEY", "v0.1-development-only-key-change-this-value-9f4c2b7a")
DEBUG = PROFILE == "development" and os.getenv("DEBUG", "True").lower() == "true"
ALLOWED_HOSTS = [
    x.strip() for x in os.getenv("ALLOWED_HOSTS", "127.0.0.1,localhost").split(",") if x.strip()
]
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "corsheaders",
    "rest_framework",
    "drf_spectacular",
    "identity",
    "cases",
    "evidence",
    "processing",
    "investigations",
    "reporting",
    "audit",
]
MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]
ROOT_URLCONF = "config.urls"
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ]
        },
    }
]
WSGI_APPLICATION = "config.wsgi.application"
DATABASE_URL = os.getenv("DATABASE_URL", "")
if DATABASE_URL and not DATABASE_URL.startswith("postgresql://"):
    raise ValueError("DATABASE_URL must be a postgresql:// URL")
if DATABASE_URL.startswith("postgresql://"):
    parsed = urlparse(DATABASE_URL)
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": parsed.path.lstrip("/"),
            "USER": parsed.username,
            "PASSWORD": parsed.password,
            "HOST": parsed.hostname,
            "PORT": parsed.port or 5432,
        }
    }
else:
    DATABASES = {
        "default": {"ENGINE": "django.db.backends.sqlite3", "NAME": BASE_DIR / "db.sqlite3"}
    }
AUTH_USER_MODEL = "identity.User"
LANGUAGE_CODE = "en-gb"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True
STATIC_URL = "static/"
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": ["rest_framework.authentication.SessionAuthentication"],
    "DEFAULT_PERMISSION_CLASSES": ["rest_framework.permissions.IsAuthenticated"],
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
}
SPECTACULAR_SETTINGS = {
    "TITLE": "P.R.O.V.E API",
    "VERSION": "0.1.0",
    "SERVE_INCLUDE_SCHEMA": False,
    "PREPROCESSING_HOOKS": ["config.schema.versioned_endpoints"],
}
CORS_ALLOWED_ORIGINS = [
    x.strip()
    for x in os.getenv("CORS_ALLOWED_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173").split(
        ","
    )
    if x.strip()
]
CSRF_TRUSTED_ORIGINS = [
    x.strip()
    for x in os.getenv("CSRF_TRUSTED_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173").split(
        ","
    )
    if x.strip()
]
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = "Lax"
CSRF_COOKIE_SAMESITE = "Lax"
SESSION_COOKIE_SECURE = not DEBUG
CSRF_COOKIE_SECURE = not DEBUG
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_REFERRER_POLICY = "same-origin"
X_FRAME_OPTIONS = "DENY"
SECURE_SSL_REDIRECT = os.getenv("SECURE_SSL_REDIRECT", "False").lower() == "true"
SECURE_HSTS_SECONDS = int(os.getenv("SECURE_HSTS_SECONDS", "0"))
SECURE_HSTS_INCLUDE_SUBDOMAINS = (
    os.getenv("SECURE_HSTS_INCLUDE_SUBDOMAINS", "False").lower() == "true"
)
SECURE_HSTS_PRELOAD = os.getenv("SECURE_HSTS_PRELOAD", "False").lower() == "true"
CELERY_BROKER_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
CELERY_RESULT_BACKEND = CELERY_BROKER_URL
CELERY_TASK_ALWAYS_EAGER = os.getenv("CELERY_TASK_ALWAYS_EAGER", "True").lower() == "true"
EVIDENCE_ROOT = Path(os.getenv("EVIDENCE_ROOT", str(BASE_DIR.parent.parent / "var/evidence")))
OUTPUT_ROOT = Path(os.getenv("OUTPUT_ROOT", str(BASE_DIR.parent.parent / "var/output")))
SYNTHETIC_ROOT = EVIDENCE_ROOT
MAX_EVIDENCE_BYTES = 64 * 1024 * 1024
MAX_EXPORT_BYTES = 32 * 1024 * 1024
PROCESSING_TIMEOUT = 30
if PROFILE == "team":
    from django.core.exceptions import ImproperlyConfigured

    if len(SECRET_KEY) < 50 or "development" in SECRET_KEY or SECRET_KEY.startswith("ChangeMe"):
        raise ImproperlyConfigured("Team profile requires a strong non-development SECRET_KEY")
    for required in (
        "DATABASE_URL",
        "REDIS_URL",
        "ALLOWED_HOSTS",
        "CSRF_TRUSTED_ORIGINS",
        "CORS_ALLOWED_ORIGINS",
        "EVIDENCE_ROOT",
        "OUTPUT_ROOT",
    ):
        if not os.getenv(required):
            raise ImproperlyConfigured(f"Team profile requires {required}")
    if (
        not parsed.hostname
        or not parsed.path.lstrip("/")
        or not parsed.username
        or not parsed.password
    ):
        raise ImproperlyConfigured("Incomplete PostgreSQL configuration")
    if "*" in ALLOWED_HOSTS or any(
        not origin.startswith("https://") for origin in CSRF_TRUSTED_ORIGINS + CORS_ALLOWED_ORIGINS
    ):
        raise ImproperlyConfigured("Team hosts and HTTPS origins must be explicit")
    if (
        urlparse(CELERY_BROKER_URL).scheme not in {"redis", "rediss"}
        or not urlparse(CELERY_BROKER_URL).hostname
    ):
        raise ImproperlyConfigured("Invalid Redis URL")
    if (
        not EVIDENCE_ROOT.is_absolute()
        or not OUTPUT_ROOT.is_absolute()
        or not EVIDENCE_ROOT.is_dir()
        or not OUTPUT_ROOT.is_dir()
    ):
        raise ImproperlyConfigured("Team storage must be existing absolute directories")
    if (
        EVIDENCE_ROOT.resolve() == OUTPUT_ROOT.resolve()
        or EVIDENCE_ROOT.resolve() in OUTPUT_ROOT.resolve().parents
        or OUTPUT_ROOT.resolve() in EVIDENCE_ROOT.resolve().parents
    ):
        raise ImproperlyConfigured("Evidence and output storage must be disjoint")
    if os.getenv("CELERY_TASK_ALWAYS_EAGER", "false").lower() != "false":
        raise ImproperlyConfigured("Team processing cannot use eager mode")
    CELERY_TASK_ALWAYS_EAGER = False
    SECURE_SSL_REDIRECT = True
    SECURE_HSTS_SECONDS = 31536000
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    CACHES = {
        "default": {
            "BACKEND": "django.core.cache.backends.redis.RedisCache",
            "LOCATION": CELERY_BROKER_URL,
        }
    }
