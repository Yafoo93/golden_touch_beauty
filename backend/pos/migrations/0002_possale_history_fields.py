import django.db.models.deletion
import pos.models
import secrets
from decimal import Decimal
from django.conf import settings
import django.core.validators
from django.db import migrations, models


def populate_references(apps, schema_editor):
    POSSale = apps.get_model("pos", "POSSale")
    for sale in POSSale.objects.filter(reference__isnull=True).iterator():
        sale.reference = f"GTS-LEGACY-{secrets.token_hex(4).upper()}"
        sale.save(update_fields=["reference"])


class Migration(migrations.Migration):
    dependencies = [("pos", "0001_initial"), migrations.swappable_dependency(settings.AUTH_USER_MODEL)]
    operations = [
        migrations.AddField(model_name="possale", name="reference", field=models.CharField(blank=True, editable=False, max_length=24, null=True)),
        migrations.RunPython(populate_references, migrations.RunPython.noop),
        migrations.AlterField(model_name="possale", name="reference", field=models.CharField(default=pos.models.pos_sale_reference, editable=False, max_length=24, unique=True)),
        migrations.AddField(model_name="possale", name="cashier", field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name="pos_sales", to=settings.AUTH_USER_MODEL)),
        migrations.AddField(model_name="possale", name="customer", field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name="pos_purchases", to=settings.AUTH_USER_MODEL)),
        migrations.AddField(model_name="possale", name="status", field=models.CharField(choices=[("draft", "Draft"), ("completed", "Completed"), ("voided", "Voided"), ("refunded", "Refunded")], default="draft", max_length=20)),
        migrations.AddField(model_name="possale", name="payment_status", field=models.CharField(default="pending", max_length=30)),
        migrations.AddField(model_name="possale", name="currency", field=models.CharField(default="GHS", max_length=3)),
        migrations.AddField(model_name="possale", name="total_amount", field=models.DecimalField(decimal_places=2, default=Decimal("0.00"), max_digits=12, validators=[django.core.validators.MinValueValidator(Decimal("0.00"))])),
        migrations.AddField(model_name="possale", name="item_count", field=models.PositiveIntegerField(default=0)),
        migrations.AddField(model_name="possale", name="completed_at", field=models.DateTimeField(blank=True, null=True)),
        migrations.AlterModelOptions(name="possale", options={"ordering": ["-completed_at", "-created_at"]}),
        migrations.AddIndex(model_name="possale", index=models.Index(fields=["branch", "status", "created_at"], name="pos_possale_branch_status_idx")),
        migrations.AddIndex(model_name="possale", index=models.Index(fields=["cashier", "created_at"], name="pos_possale_cashier_idx")),
    ]
