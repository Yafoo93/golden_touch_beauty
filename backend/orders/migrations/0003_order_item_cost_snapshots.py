from decimal import Decimal

from django.db import migrations, models
import django.core.validators


def backfill_order_costs(apps, schema_editor):
    OrderItem = apps.get_model("orders", "OrderItem")
    for item in OrderItem.objects.select_related("product_variant").iterator():
        unit_cost = item.product_variant.cost_price
        item.unit_cost = unit_cost
        item.line_cost = unit_cost * item.quantity
        item.save(update_fields=["unit_cost", "line_cost"])


class Migration(migrations.Migration):
    dependencies = [("orders", "0002_orderitem_stockreservation_order_cancelled_at_and_more")]
    operations = [
        migrations.AddField(model_name="orderitem", name="unit_cost", field=models.DecimalField(decimal_places=2, default=Decimal("0.00"), max_digits=12, validators=[django.core.validators.MinValueValidator(Decimal("0.00"))])),
        migrations.AddField(model_name="orderitem", name="line_cost", field=models.DecimalField(decimal_places=2, default=Decimal("0.00"), max_digits=12, validators=[django.core.validators.MinValueValidator(Decimal("0.00"))])),
        migrations.RunPython(backfill_order_costs, migrations.RunPython.noop),
    ]
