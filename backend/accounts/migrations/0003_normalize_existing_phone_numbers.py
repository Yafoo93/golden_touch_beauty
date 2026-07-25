import re

from django.db import migrations


def normalize(value):
    raw = str(value or "").strip()
    digits = re.sub(r"\D", "", raw)
    if not digits:
        return ""
    if raw.startswith("00"):
        return f"+{digits[2:]}"
    if raw.startswith("+"):
        return f"+{digits}"
    if digits.startswith("233"):
        return f"+{digits}"
    if digits.startswith("0"):
        return f"+233{digits[1:]}"
    return f"+{digits}"


def normalize_users(apps, schema_editor):
    User = apps.get_model("accounts", "User")
    for user in User.objects.all().iterator():
        normalized = normalize(user.phone_number)
        if normalized != user.phone_number:
            user.phone_number = normalized
            user.save(update_fields=["phone_number"])


class Migration(migrations.Migration):
    dependencies = [
        ("accounts", "0002_user_email_verified_at"),
    ]

    operations = [
        migrations.RunPython(normalize_users, migrations.RunPython.noop),
    ]
