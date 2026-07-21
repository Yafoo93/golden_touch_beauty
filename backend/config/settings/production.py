from django.core.exceptions import ImproperlyConfigured

from .base import *  # noqa: F403


if DEBUG:  # noqa: F405
    raise ImproperlyConfigured("DJANGO_DEBUG must be False in production.")

if SECRET_KEY.startswith("replace-"):  # noqa: F405
    raise ImproperlyConfigured("Set a secure DJANGO_SECRET_KEY in production.")

SECURE_HSTS_SECONDS = env.int(  # noqa: F405
    "DJANGO_SECURE_HSTS_SECONDS",
    default=31536000,
)
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True

EMAIL_BACKEND = env(  # noqa: F405
    "DJANGO_EMAIL_BACKEND",
    default="django.core.mail.backends.smtp.EmailBackend",
)
