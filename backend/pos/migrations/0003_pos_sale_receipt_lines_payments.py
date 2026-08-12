import django.core.validators
import django.db.models.deletion
import pos.models
import secrets
import uuid
from decimal import Decimal
from django.db import migrations, models


def populate_receipt_references(apps, schema_editor):
    POSSale = apps.get_model("pos", "POSSale")
    for sale in POSSale.objects.filter(receipt_reference__isnull=True).iterator():
        sale.receipt_reference = f"GTR-POS-LEGACY-{secrets.token_hex(4).upper()}"
        sale.save(update_fields=["receipt_reference"])


class Migration(migrations.Migration):
    dependencies = [("pos", "0002_possale_history_fields")]
    operations = [
        migrations.AddField(model_name="possale", name="receipt_reference", field=models.CharField(blank=True, editable=False, max_length=28, null=True)),
        migrations.RunPython(populate_receipt_references, migrations.RunPython.noop),
        migrations.AlterField(model_name="possale", name="receipt_reference", field=models.CharField(default=pos.models.pos_receipt_reference, editable=False, max_length=28, unique=True)),
        migrations.CreateModel(
            name="POSSaleLine",
            fields=[
                ("id", models.UUIDField(primary_key=True, serialize=False, editable=False, default=uuid.uuid4)),
                ("created_at", models.DateTimeField(auto_now_add=True)), ("updated_at", models.DateTimeField(auto_now=True)),
                ("item_type", models.CharField(choices=[("product", "Product"), ("service", "Service")], max_length=20)),
                ("item_reference", models.CharField(max_length=100)), ("name", models.CharField(max_length=180)),
                ("option_name", models.CharField(blank=True, max_length=150)), ("sku", models.CharField(blank=True, max_length=80)),
                ("quantity", models.PositiveIntegerField()),
                ("unit_price", models.DecimalField(decimal_places=2, max_digits=12, validators=[django.core.validators.MinValueValidator(Decimal("0.00"))])),
                ("line_total", models.DecimalField(decimal_places=2, max_digits=12, validators=[django.core.validators.MinValueValidator(Decimal("0.00"))])),
                ("sale", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="lines", to="pos.possale")),
            ], options={"ordering": ["created_at"]},
        ),
        migrations.CreateModel(
            name="POSPaymentEntry",
            fields=[
                ("id", models.UUIDField(primary_key=True, serialize=False, editable=False, default=uuid.uuid4)),
                ("created_at", models.DateTimeField(auto_now_add=True)), ("updated_at", models.DateTimeField(auto_now=True)),
                ("method", models.CharField(max_length=40)), ("reference", models.CharField(blank=True, max_length=150)),
                ("amount", models.DecimalField(decimal_places=2, max_digits=12, validators=[django.core.validators.MinValueValidator(Decimal("0.00"))])),
                ("status", models.CharField(default="succeeded", max_length=20)),
                ("sale", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="payment_entries", to="pos.possale")),
            ], options={"ordering": ["created_at"]},
        ),
    ]
