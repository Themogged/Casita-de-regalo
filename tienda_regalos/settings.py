import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent


def env_bool(name, default=False):
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


SECRET_KEY = os.getenv(
    "DJANGO_SECRET_KEY",
    "dev-only-change-this-before-production-2026",
)

DEBUG = env_bool("DJANGO_DEBUG", True)


def env_list(name, default=""):
    value = os.getenv(name)
    raw = value if value is not None else default
    return [item.strip() for item in raw.split(",") if item.strip()]


ALLOWED_HOSTS = list(
    dict.fromkeys(
        env_list(
            "DJANGO_ALLOWED_HOSTS",
            "casita-de-regalos.onrender.com",
        )
        + ["127.0.0.1", "localhost", "0.0.0.0", "[::1]", "testserver"]
    )
)

CSRF_TRUSTED_ORIGINS = list(
    dict.fromkeys(
        env_list(
            "DJANGO_CSRF_TRUSTED_ORIGINS",
            "https://casita-de-regalos.onrender.com",
        )
        + [
            "http://127.0.0.1:8000",
            "http://localhost:8000",
            "http://0.0.0.0:8000",
        ]
    )
)


INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "productos",
    "carrito",
    "categorias",
    "pedidos",
    "cuentas",
    "asistente",
]


MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.middleware.gzip.GZipMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",  # 🔥 IMPORTANTE
    "tienda_regalos.middleware.AdminRateLimitMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "tienda_regalos.middleware.SecurityHeadersMiddleware",
]


ROOT_URLCONF = "tienda_regalos.urls"


TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "Templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.template.context_processors.csrf",
                "django.template.context_processors.media",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "carrito.context_processors.carrito_total",
                "productos.context_processors.categorias_menu",
                "productos.context_processors.business_links",
                "productos.context_processors.seo_context",
                "asistente.context_processors.assistant_account_context",
            ],
        },
    },
]


WSGI_APPLICATION = "tienda_regalos.wsgi.application"


DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}


AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]


LANGUAGE_CODE = "es-co"
TIME_ZONE = "America/Bogota"
USE_I18N = True
USE_TZ = True


# 🔥 STATIC FILES (CSS, JS, etc)
STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"

STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        "BACKEND": (
            "django.contrib.staticfiles.storage.StaticFilesStorage"
            if DEBUG
            else "whitenoise.storage.CompressedManifestStaticFilesStorage"
        ),
    },
}
WHITENOISE_MANIFEST_STRICT = False


# 🔥 MEDIA (IMÁGENES SUBIDAS)
MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"


DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"


CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        "LOCATION": "tienda-regalos-security",
    }
}


SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = "Lax"
SESSION_COOKIE_AGE = int(os.getenv("DJANGO_SESSION_COOKIE_AGE", str(60 * 60 * 24 * 30)))
SESSION_EXPIRE_AT_BROWSER_CLOSE = env_bool(
    "DJANGO_SESSION_EXPIRE_AT_BROWSER_CLOSE",
    False,
)

LOGIN_URL = "login"
LOGIN_REDIRECT_URL = "account_profile"
LOGOUT_REDIRECT_URL = "inicio"

CSRF_COOKIE_HTTPONLY = True
CSRF_COOKIE_SAMESITE = "Lax"

X_FRAME_OPTIONS = "DENY"
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_REFERRER_POLICY = "same-origin"
SECURE_CROSS_ORIGIN_OPENER_POLICY = "same-origin"
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")


ADMIN_LOGIN_MAX_ATTEMPTS = int(os.getenv("DJANGO_ADMIN_LOGIN_MAX_ATTEMPTS", "5"))
ADMIN_LOGIN_BLOCK_MINUTES = int(os.getenv("DJANGO_ADMIN_LOGIN_BLOCK_MINUTES", "15"))
CUSTOMER_LOGIN_MAX_ATTEMPTS = int(os.getenv("DJANGO_CUSTOMER_LOGIN_MAX_ATTEMPTS", "8"))
CUSTOMER_LOGIN_BLOCK_MINUTES = int(os.getenv("DJANGO_CUSTOMER_LOGIN_BLOCK_MINUTES", "15"))
TRUST_X_FORWARDED_FOR = env_bool("DJANGO_TRUST_X_FORWARDED_FOR", False)
TELEMETRY_EVENTS_PER_MINUTE = int(os.getenv("DJANGO_TELEMETRY_EVENTS_PER_MINUTE", "90"))
BUSINESS_WHATSAPP_NUMBER = os.getenv("BUSINESS_WHATSAPP_NUMBER", "573116262155")

EMAIL_BACKEND = os.getenv(
    "DJANGO_EMAIL_BACKEND",
    "django.core.mail.backends.console.EmailBackend",
)
EMAIL_HOST = os.getenv("DJANGO_EMAIL_HOST", "")
EMAIL_PORT = int(os.getenv("DJANGO_EMAIL_PORT", "587"))
EMAIL_HOST_USER = os.getenv("DJANGO_EMAIL_HOST_USER", "")
EMAIL_HOST_PASSWORD = os.getenv("DJANGO_EMAIL_HOST_PASSWORD", "")
EMAIL_USE_TLS = env_bool("DJANGO_EMAIL_USE_TLS", True)
EMAIL_TIMEOUT = int(os.getenv("DJANGO_EMAIL_TIMEOUT", "15"))
DEFAULT_FROM_EMAIL = os.getenv("DJANGO_DEFAULT_FROM_EMAIL", "Casita de Regalos <no-reply@localhost>")

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "simple": {"format": "{levelname} {name} {message}", "style": "{"},
    },
    "handlers": {
        "console": {"class": "logging.StreamHandler", "formatter": "simple"},
    },
    "loggers": {
        "storefront.events": {
            "handlers": ["console"],
            "level": os.getenv("DJANGO_TELEMETRY_LOG_LEVEL", "INFO"),
            "propagate": False,
        },
    },
}


# 🔥 PRODUCCIÓN
SESSION_COOKIE_SECURE = not DEBUG
CSRF_COOKIE_SECURE = not DEBUG
SECURE_SSL_REDIRECT = env_bool("DJANGO_SECURE_SSL_REDIRECT", not DEBUG)
SECURE_HSTS_SECONDS = 31536000 if not DEBUG else 0
SECURE_HSTS_INCLUDE_SUBDOMAINS = not DEBUG
SECURE_HSTS_PRELOAD = not DEBUG
