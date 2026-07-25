import re

from django.db import migrations


PHONE_FIELDS = (
    "telephone_number",
    "secondary_telephone_number",
    "whatsapp_number",
    "secondary_whatsapp_number",
)


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


def normalize_branches(apps, schema_editor):
    Branch = apps.get_model("branches", "Branch")
    for branch in Branch.objects.all().iterator():
        changed = []
        for field_name in PHONE_FIELDS:
            current = getattr(branch, field_name)
            normalized = normalize(current)
            if normalized != current:
                setattr(branch, field_name, normalized)
                changed.append(field_name)
        if changed:
            branch.save(update_fields=changed)


class Migration(migrations.Migration):
    dependencies = [
        ("branches", "0003_branchstaffassignment"),
    ]

    operations = [
        migrations.RunPython(normalize_branches, migrations.RunPython.noop),
    ]
