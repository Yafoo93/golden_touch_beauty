from decimal import Decimal

from django.db import migrations, models
import django.core.validators


def backfill_pos_costs(apps, schema_editor):
    POSSaleLine = apps.get_model("pos", "POSSaleLine")
    ProductVariant = apps.get_model("products", "ProductVariant")
    variants = {variant.sku: variant for variant in ProductVariant.objects.all()}
    for line in POSSaleLine.objects.filter(item_type="product").iterator():
        variant = variants.get(line.sku)
        if variant:
            line.unit_cost = variant.cost_price
            line.line_cost = variant.cost_price * line.quantity
            line.save(update_fields=["unit_cost", "line_cost"])


class Migration(migrations.Migration):
    dependencies = [("pos", "0003_pos_sale_receipt_lines_payments"), ("products", "0004_customercartitem")]
    operations = [
        migrations.AddField(model_name="possaleline", name="unit_cost", field=models.DecimalField(decimal_places=2, default=Decimal("0.00"), max_digits=12, validators=[django.core.validators.MinValueValidator(Decimal("0.00"))])),
        migrations.AddField(model_name="possaleline", name="line_cost", field=models.DecimalField(decimal_places=2, default=Decimal("0.00"), max_digits=12, validators=[django.core.validators.MinValueValidator(Decimal("0.00"))])),
        migrations.RunPython(backfill_pos_costs, migrations.RunPython.noop),
    ]
