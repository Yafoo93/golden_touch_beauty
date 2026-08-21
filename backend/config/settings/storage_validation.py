from urllib.parse import urlsplit

from django.core.exceptions import ImproperlyConfigured


def validate_r2_settings(
    *,
    endpoint_url: str,
    public_bucket: str,
    private_bucket: str,
    public_custom_domain: str,
    private_url_expiry: int,
) -> None:
    """Reject ambiguous or unsafe R2 configuration without logging secrets."""
    errors: list[str] = []
    endpoint = urlsplit(endpoint_url)

    if endpoint.scheme != "https" or not endpoint.hostname:
        errors.append("R2_ENDPOINT_URL must be a valid HTTPS URL.")
    if public_bucket == private_bucket:
        errors.append("Public and private R2 buckets must be different.")
    if any("/" in bucket or not bucket.strip() for bucket in (public_bucket, private_bucket)):
        errors.append("R2 bucket names must not contain slashes or be empty.")
    if (
        "://" in public_custom_domain
        or "/" in public_custom_domain
        or not public_custom_domain.strip()
    ):
        errors.append("R2_PUBLIC_CUSTOM_DOMAIN must be a hostname without a scheme or path.")
    if not 60 <= private_url_expiry <= 3600:
        errors.append("R2_PRIVATE_URL_EXPIRY must be between 60 and 3600 seconds.")

    if errors:
        raise ImproperlyConfigured("R2 configuration is unsafe: " + " ".join(errors))
