from pathlib import Path

import environ

from .storage_validation import validate_r2_settings


BASE_DIR = Path(__file__).resolve().parents[2]

env = environ.Env(
    DJANGO_DEBUG=(bool, False),
    DJANGO_ALLOWED_HOSTS=(list, ["127.0.0.1", "localhost"]),
    DJANGO_CSRF_TRUSTED_ORIGINS=(list, []),
    DJANGO_SECURE_SSL_REDIRECT=(bool, False),
    DJANGO_SESSION_COOKIE_SECURE=(bool, False),
    DJANGO_CSRF_COOKIE_SECURE=(bool, False),
    DJANGO_LOG_LEVEL=(str, "INFO"),
    USE_R2_STORAGE=(bool, False),
)
environ.Env.read_env(BASE_DIR / ".env")

SECRET_KEY = env("DJANGO_SECRET_KEY")
DEBUG = env.bool("DJANGO_DEBUG")
ALLOWED_HOSTS = env.list("DJANGO_ALLOWED_HOSTS")

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "corsheaders",
    "rest_framework",
    "django_filters",
    "drf_spectacular",
    "drf_spectacular_sidecar",
    "storages",
    "core",
    "accounts",
    "branches",
    "customers",
    "services",
    "bookings",
    "products",
    "inventory",
    "orders",
    "pos",
    "payments",
    "expenses",
    "notifications",
    "reports",
    "auditlog",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "core.middleware.RequestLoggingMiddleware",
    "corsheaders.middleware.CorsMiddleware",
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
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"

database_url = env("DATABASE_URL", default="")

if database_url:
    # Render supplies its managed PostgreSQL connection as one URL. Supporting
    # it directly also keeps credentials out of individual dashboard fields.
    DATABASES = {
        "default": env.db_url_config(database_url)
    }
    DATABASES["default"]["CONN_MAX_AGE"] = 60
    DATABASES["default"].setdefault("OPTIONS", {})["connect_timeout"] = 10
else:
    # Local development continues to use the explicit variables documented in
    # backend/.env.example and compose.yaml.
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": env("POSTGRES_DB"),
            "USER": env("POSTGRES_USER"),
            "PASSWORD": env("POSTGRES_PASSWORD"),
            "HOST": env("POSTGRES_HOST", default="127.0.0.1"),
            "PORT": env.int("POSTGRES_PORT", default=5432),
            "CONN_MAX_AGE": 60,
            "OPTIONS": {"connect_timeout": 10},
        }
    }

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": (
            "django.contrib.auth.password_validation."
            "UserAttributeSimilarityValidator"
        )
    },
    {
        "NAME": (
            "django.contrib.auth.password_validation."
            "MinimumLengthValidator"
        )
    },
    {
        "NAME": (
            "django.contrib.auth.password_validation."
            "CommonPasswordValidator"
        )
    },
    {
        "NAME": (
            "django.contrib.auth.password_validation."
            "NumericPasswordValidator"
        )
    },
]

LANGUAGE_CODE = "en-gb"
TIME_ZONE = "Africa/Accra"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"
USE_R2_STORAGE = env.bool("USE_R2_STORAGE")

if USE_R2_STORAGE:
    R2_ENDPOINT_URL = env("R2_ENDPOINT_URL")
    R2_PUBLIC_BUCKET = env("R2_PUBLIC_BUCKET")
    R2_PUBLIC_ACCESS_KEY_ID = env("R2_PUBLIC_ACCESS_KEY_ID")
    R2_PUBLIC_SECRET_ACCESS_KEY = env("R2_PUBLIC_SECRET_ACCESS_KEY")
    R2_PUBLIC_CUSTOM_DOMAIN = env("R2_PUBLIC_CUSTOM_DOMAIN")
    R2_PRIVATE_BUCKET = env("R2_PRIVATE_BUCKET")
    R2_PRIVATE_ACCESS_KEY_ID = env("R2_PRIVATE_ACCESS_KEY_ID")
    R2_PRIVATE_SECRET_ACCESS_KEY = env("R2_PRIVATE_SECRET_ACCESS_KEY")
    R2_PRIVATE_URL_EXPIRY = env.int("R2_PRIVATE_URL_EXPIRY", default=300)

    validate_r2_settings(
        endpoint_url=R2_ENDPOINT_URL,
        public_bucket=R2_PUBLIC_BUCKET,
        private_bucket=R2_PRIVATE_BUCKET,
        public_custom_domain=R2_PUBLIC_CUSTOM_DOMAIN,
        private_url_expiry=R2_PRIVATE_URL_EXPIRY,
    )

    common_r2_options = {
        "endpoint_url": R2_ENDPOINT_URL,
        "region_name": "auto",
        "signature_version": "s3v4",
        "default_acl": None,
        "file_overwrite": False,
    }
    public_storage = {
        "BACKEND": "storages.backends.s3.S3Storage",
        "OPTIONS": {
            **common_r2_options,
            "bucket_name": R2_PUBLIC_BUCKET,
            "access_key": R2_PUBLIC_ACCESS_KEY_ID,
            "secret_key": R2_PUBLIC_SECRET_ACCESS_KEY,
            "custom_domain": R2_PUBLIC_CUSTOM_DOMAIN,
            "querystring_auth": False,
            "url_protocol": "https:",
            "object_parameters": {
                "CacheControl": "public, max-age=86400",
            },
        },
    }
    private_storage = {
        "BACKEND": "storages.backends.s3.S3Storage",
        "OPTIONS": {
            **common_r2_options,
            "bucket_name": R2_PRIVATE_BUCKET,
            "access_key": R2_PRIVATE_ACCESS_KEY_ID,
            "secret_key": R2_PRIVATE_SECRET_ACCESS_KEY,
            "custom_domain": None,
            "querystring_auth": True,
            "querystring_expire": R2_PRIVATE_URL_EXPIRY,
        },
    }
else:
    local_storage = {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
        "OPTIONS": {
            "location": MEDIA_ROOT,
            "base_url": MEDIA_URL,
        },
    }
    public_storage = local_storage
    private_storage = local_storage

STORAGES = {
    # Default to private storage so newly added upload fields fail closed unless
    # they are deliberately assigned to the public-media alias.
    "default": private_storage,
    "public_media": public_storage,
    "private_media": private_storage,
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
}

AUTH_USER_MODEL = "accounts.User"
AUTHENTICATION_BACKENDS = ["accounts.backends.EmailOrPhoneBackend"]

# Browser requests reach Django through a same-origin Next.js rewrite. Django
# sessions stay in HTTP-only cookies and state-changing requests retain CSRF
# protection. Direct cross-origin access is intended only for local development.
FRONTEND_URL = env("FRONTEND_URL", default="http://localhost:3000").rstrip("/")
CORS_ALLOWED_ORIGINS = [FRONTEND_URL]
CORS_ALLOW_CREDENTIALS = True
CSRF_TRUSTED_ORIGINS = [
    origin.rstrip("/")
    for origin in env.list("DJANGO_CSRF_TRUSTED_ORIGINS", default=[FRONTEND_URL])
]

SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SECURE = env.bool("DJANGO_SESSION_COOKIE_SECURE")
SESSION_COOKIE_SAMESITE = "Lax"
SESSION_COOKIE_PATH = "/"
SESSION_COOKIE_DOMAIN = None
SESSION_ENGINE = "django.contrib.sessions.backends.db"
SESSION_SAVE_EVERY_REQUEST = False
CSRF_COOKIE_SECURE = env.bool("DJANGO_CSRF_COOKIE_SECURE")
CSRF_COOKIE_SAMESITE = "Lax"
# The frontend reads this cookie only to echo the token in the X-CSRFToken
# header. It contains no authentication credential; the session cookie remains
# HTTP-only.
CSRF_COOKIE_HTTPONLY = False

SECURE_SSL_REDIRECT = env.bool("DJANGO_SECURE_SSL_REDIRECT")
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = "DENY"

REST_FRAMEWORK = {
    "EXCEPTION_HANDLER": "core.exceptions.api_exception_handler",
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "accounts.authentication.CsrfProtectedSessionAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],
    "DEFAULT_FILTER_BACKENDS": [
        "django_filters.rest_framework.DjangoFilterBackend",
        "rest_framework.filters.SearchFilter",
        "rest_framework.filters.OrderingFilter",
    ],
    "DEFAULT_PAGINATION_CLASS": (
        "rest_framework.pagination.PageNumberPagination"
    ),
    "PAGE_SIZE": 20,
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    "DEFAULT_THROTTLE_CLASSES": [
        "rest_framework.throttling.AnonRateThrottle",
        "rest_framework.throttling.UserRateThrottle",
    ],
    "DEFAULT_THROTTLE_RATES": {
        "anon": "100/minute",
        "user": "1000/minute",
        "auth-register": "5/hour",
        "auth-login": "10/minute",
        "auth-verify": "5/hour",
        "auth-reset": "5/hour",
        "payment-customer": "10/minute",
        "payment-pos": "30/minute",
    },
}

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

SPECTACULAR_SETTINGS = {
    "TITLE": "Golden Touch Beauty Centre API",
    "DESCRIPTION": (
        "API for bookings, products, inventory, POS, payments and branch "
        "management."
    ),
    "VERSION": "1.0.0",
    "SERVE_INCLUDE_SCHEMA": False,
    "SWAGGER_UI_DIST": "SIDECAR",
    "SWAGGER_UI_FAVICON_HREF": "SIDECAR",
    "REDOC_DIST": "SIDECAR",
}

DEFAULT_FROM_EMAIL = env(
    "DEFAULT_FROM_EMAIL",
    default="Golden Touch Beauty Centre <noreply@goldentouch.local>",
)
EMAIL_HOST = env("DJANGO_EMAIL_HOST", default="localhost")
EMAIL_PORT = env.int("DJANGO_EMAIL_PORT", default=587)
EMAIL_HOST_USER = env("DJANGO_EMAIL_HOST_USER", default="")
EMAIL_HOST_PASSWORD = env("DJANGO_EMAIL_HOST_PASSWORD", default="")
EMAIL_USE_TLS = env.bool("DJANGO_EMAIL_USE_TLS", default=True)
EMAIL_USE_SSL = env.bool("DJANGO_EMAIL_USE_SSL", default=False)
EMAIL_TIMEOUT = env.int("DJANGO_EMAIL_TIMEOUT", default=15)
EMAIL_JOBS_EAGER = env.bool("EMAIL_JOBS_EAGER", default=False)
EMAIL_VERIFICATION_MAX_AGE_SECONDS = env.int(
    "EMAIL_VERIFICATION_MAX_AGE_SECONDS",
    default=86400,
)

# JSON stdout logs work locally and with container/cloud log collectors. Values
# such as request bodies, cookies, authorization headers, and query strings are
# intentionally excluded to avoid recording credentials or customer data.
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "json": {"()": "core.logging.JsonFormatter"},
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "json",
        },
        "null": {"class": "logging.NullHandler"},
    },
    "root": {
        "handlers": ["console"],
        "level": env("DJANGO_LOG_LEVEL"),
    },
    "loggers": {
        "django.server": {
            "handlers": ["console"],
            "level": env("DJANGO_LOG_LEVEL"),
            "propagate": False,
        },
        # RequestLoggingMiddleware already records the same event with a
        # correlation ID and duration, so suppress Django's duplicate line.
        "django.request": {
            "handlers": ["null"],
            "propagate": False,
        },
        "golden_touch": {
            "handlers": ["console"],
            "level": env("DJANGO_LOG_LEVEL"),
            "propagate": False,
        },
    },
}
