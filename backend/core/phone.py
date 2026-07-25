import re

E164_PATTERN = re.compile(r"^\+[1-9]\d{8,14}$")


def normalize_phone_number(value: str | None, default_country_code: str = "233") -> str:
    """Return a consistently formatted international phone number."""
    if value is None:
        return ""

    raw = str(value).strip()
    if not raw:
        return ""

    digits = re.sub(r"\D", "", raw)
    if not digits:
        return ""
    if raw.startswith("00"):
        return f"+{digits[2:]}"
    if raw.startswith("+"):
        return f"+{digits}"
    if digits.startswith(default_country_code):
        return f"+{digits}"
    if digits.startswith("0"):
        return f"+{default_country_code}{digits[1:]}"
    return f"+{digits}"


def is_international_phone_number(value: str) -> bool:
    return bool(E164_PATTERN.fullmatch(value))
