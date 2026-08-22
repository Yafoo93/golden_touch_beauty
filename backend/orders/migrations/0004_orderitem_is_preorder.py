from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("orders", "0003_order_item_cost_snapshots")]
    operations = [migrations.AddField(model_name="orderitem", name="is_preorder", field=models.BooleanField(default=False))]
