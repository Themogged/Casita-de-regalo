import os

from django.core.exceptions import ImproperlyConfigured

from .settings import *  # noqa: F401,F403


def env_bool(name, default=False):
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def env_list(name, default=""):
    value = os.getenv(name)
    raw = value if value is not None else default
    return [item.strip() for item in raw.split(",") if item.strip()]


PYTHONANYWHERE_HOST = os.getenv("PYTHONANYWHERE_HOST", "daxian7.pythonanywhere.com").strip()

DEBUG = env_bool("DJANGO_DEBUG", False)

if not os.getenv("DJANGO_SECRET_KEY") or SECRET_KEY.startswith("dev-only-"):
    raise ImproperlyConfigured("DJANGO_SECRET_KEY debe configurarse con una clave segura en producción.")

ALLOWED_HOSTS = list(
    dict.fromkeys(
        env_list("DJANGO_ALLOWED_HOSTS", PYTHONANYWHERE_HOST)
        + ["127.0.0.1", "localhost", "0.0.0.0", "[::1]", "testserver"]
    )
)

CSRF_TRUSTED_ORIGINS = list(
    dict.fromkeys(
        env_list("DJANGO_CSRF_TRUSTED_ORIGINS", f"https://{PYTHONANYWHERE_HOST}")
        + [
            "http://127.0.0.1:8000",
            "http://localhost:8000",
            "http://0.0.0.0:8000",
        ]
    )
)

SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_SSL_REDIRECT = env_bool("DJANGO_SECURE_SSL_REDIRECT", True)
SECURE_HSTS_SECONDS = int(os.getenv("DJANGO_SECURE_HSTS_SECONDS", "31536000"))
SECURE_HSTS_INCLUDE_SUBDOMAINS = env_bool("DJANGO_SECURE_HSTS_INCLUDE_SUBDOMAINS", True)
SECURE_HSTS_PRELOAD = env_bool("DJANGO_SECURE_HSTS_PRELOAD", True)

EMAIL_BACKEND = os.getenv(
    "DJANGO_EMAIL_BACKEND",
    "django.core.mail.backends.smtp.EmailBackend",
)
EMAIL_HOST = os.getenv("DJANGO_EMAIL_HOST", "smtp.gmail.com")
EMAIL_PORT = int(os.getenv("DJANGO_EMAIL_PORT", "587"))
EMAIL_HOST_USER = os.getenv("DJANGO_EMAIL_HOST_USER", "").strip()
EMAIL_HOST_PASSWORD = os.getenv("DJANGO_EMAIL_HOST_PASSWORD", "")
EMAIL_USE_TLS = env_bool("DJANGO_EMAIL_USE_TLS", True)
EMAIL_TIMEOUT = int(os.getenv("DJANGO_EMAIL_TIMEOUT", "15"))
DEFAULT_FROM_EMAIL = os.getenv(
    "DJANGO_DEFAULT_FROM_EMAIL",
    f"Casita de Regalos <{EMAIL_HOST_USER}>" if EMAIL_HOST_USER else "Casita de Regalos",
)

STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
}
