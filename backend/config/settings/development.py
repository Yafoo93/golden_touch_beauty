from .base import *  # noqa: F403


# Local browsers may use either hostname. Next proxies the original Origin
# header to Django, so both must be trusted even though the API request itself
# arrives from the same machine.
_LOCAL_FRONTEND_ORIGINS = ("http://localhost:3000", "http://127.0.0.1:3000")
CORS_ALLOWED_ORIGINS = list(dict.fromkeys([*CORS_ALLOWED_ORIGINS, *_LOCAL_FRONTEND_ORIGINS]))  # noqa: F405
CSRF_TRUSTED_ORIGINS = list(dict.fromkeys([*CSRF_TRUSTED_ORIGINS, *_LOCAL_FRONTEND_ORIGINS]))  # noqa: F405


EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
