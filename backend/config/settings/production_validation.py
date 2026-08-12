from urllib.parse import urlsplit

from django.core.exceptions import ImproperlyConfigured


LOCAL_HOSTS = {"127.0.0.1", "localhost", "[::1]", "::1"}


def _is_https_origin(value: str) -> bool:
    parsed = urlsplit(value)
    return bool(
        parsed.scheme == "https"
        and parsed.hostname
        and parsed.path in {"", "/"}
        and not parsed.query
        and not parsed.fragment
        and not parsed.username
        and not parsed.password
    )


def validate_production_settings(
    *,
    secret_key: str,
    allowed_hosts: list[str],
    csrf_trusted_origins: list[str],
    frontend_url: str,
    database_engine: str,
) -> None:
    """Refuse to start with development or ambiguous production settings."""
    errors: list[str] = []

    if len(secret_key) < 50 or secret_key.startswith("replace-"):
        errors.append("DJANGO_SECRET_KEY must be a unique value of at least 50 characters.")

    normalized_hosts = {host.strip().lower() for host in allowed_hosts if host.strip()}
    if not normalized_hosts:
        errors.append("DJANGO_ALLOWED_HOSTS must contain the deployed backend hostname.")
    if "*" in normalized_hosts:
        errors.append("DJANGO_ALLOWED_HOSTS must not use a wildcard in production.")
    if normalized_hosts & LOCAL_HOSTS:
        errors.append("DJANGO_ALLOWED_HOSTS must not contain local-development hosts.")
    if any("://" in host or "/" in host for host in normalized_hosts):
        errors.append("DJANGO_ALLOWED_HOSTS entries must be hostnames, not URLs.")

    frontend_origin = frontend_url.rstrip("/")
    if not _is_https_origin(frontend_origin):
        errors.append("FRONTEND_URL must be a public HTTPS origin without a path.")

    normalized_csrf_origins = {
        origin.strip().rstrip("/") for origin in csrf_trusted_origins if origin.strip()
    }
    if not normalized_csrf_origins:
        errors.append("DJANGO_CSRF_TRUSTED_ORIGINS must not be empty in production.")
    elif any(not _is_https_origin(origin) for origin in normalized_csrf_origins):
        errors.append("Every CSRF trusted origin must be a public HTTPS origin.")
    if frontend_origin not in normalized_csrf_origins:
        errors.append("FRONTEND_URL must be included in DJANGO_CSRF_TRUSTED_ORIGINS.")

    if not database_engine.endswith("postgresql"):
        errors.append("Production DATABASE_URL must use PostgreSQL.")

    if errors:
        raise ImproperlyConfigured("Production configuration is unsafe: " + " ".join(errors))
