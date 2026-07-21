import secrets

from django.utils import timezone


def generate_reference(prefix: str) -> str:
    """Return a readable, non-sequential public reference.

    Database uniqueness constraints remain mandatory on the consuming model.
    """

    date_part = timezone.now().strftime("%Y%m%d")
    random_part = secrets.token_hex(4).upper()
    return f"{prefix.upper()}-{date_part}-{random_part}"

