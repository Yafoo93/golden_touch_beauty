from django.core.exceptions import ImproperlyConfigured

from .base import *  # noqa: F403
from .production_validation import validate_production_settings


if DEBUG:  # noqa: F405
    raise ImproperlyConfigured("DJANGO_DEBUG must be False in production.")

validate_production_settings(
    secret_key=SECRET_KEY,  # noqa: F405
    allowed_hosts=ALLOWED_HOSTS,  # noqa: F405
    csrf_trusted_origins=CSRF_TRUSTED_ORIGINS,  # noqa: F405
    frontend_url=FRONTEND_URL,  # noqa: F405
    database_engine=DATABASES["default"]["ENGINE"],  # noqa: F405
)

SECURE_HSTS_SECONDS = env.int(  # noqa: F405
    "DJANGO_SECURE_HSTS_SECONDS",
    default=31536000,
)
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
# Render terminates TLS before forwarding traffic to Gunicorn. Trust only the
# forwarded protocol marker needed to recover the original request scheme;
# host routing continues to be checked against ALLOWED_HOSTS.
USE_X_FORWARDED_HOST = False
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True

EMAIL_BACKEND = env(  # noqa: F405
    "DJANGO_EMAIL_BACKEND",
    default="django.core.mail.backends.smtp.EmailBackend",
)
