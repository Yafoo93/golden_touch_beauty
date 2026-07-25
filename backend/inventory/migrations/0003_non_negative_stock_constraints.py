from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("inventory", "0002_stockmovement"),
    ]

    operations = [
        migrations.AddConstraint(
            model_name="branchinventory",
            constraint=models.CheckConstraint(
                condition=models.Q(("quantity_on_hand__gte", 0)),
                name="inventory_on_hand_not_negative",
            ),
        ),
        migrations.AddConstraint(
            model_name="branchinventory",
            constraint=models.CheckConstraint(
                condition=models.Q(("quantity_reserved__gte", 0)),
                name="inventory_reserved_not_negative",
            ),
        ),
        migrations.AddConstraint(
            model_name="branchinventory",
            constraint=models.CheckConstraint(
                condition=models.Q(("reorder_level__gte", 0)),
                name="inventory_reorder_level_not_negative",
            ),
        ),
        migrations.AddConstraint(
            model_name="stockmovement",
            constraint=models.CheckConstraint(
                condition=models.Q(("quantity_on_hand_after__gte", 0)),
                name="stock_movement_on_hand_after_not_negative",
            ),
        ),
        migrations.AddConstraint(
            model_name="stockmovement",
            constraint=models.CheckConstraint(
                condition=models.Q(("quantity_reserved_after__gte", 0)),
                name="stock_movement_reserved_after_not_negative",
            ),
        ),
        migrations.AddConstraint(
            model_name="stockmovement",
            constraint=models.CheckConstraint(
                condition=models.Q(
                    ("quantity_reserved_after__lte", models.F("quantity_on_hand_after"))
                ),
                name="stock_movement_reserved_not_above_on_hand",
            ),
        ),
    ]
