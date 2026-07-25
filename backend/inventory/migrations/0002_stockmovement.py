import django.db.models.deletion
import uuid
from django.conf import settings
from django.db import migrations, models


def create_opening_movements(apps, schema_editor):
    BranchInventory = apps.get_model("inventory", "BranchInventory")
    StockMovement = apps.get_model("inventory", "StockMovement")
    StockMovement.objects.bulk_create(
        [
            StockMovement(
                inventory=inventory,
                movement_type="opening",
                quantity_on_hand_change=inventory.quantity_on_hand,
                quantity_reserved_change=inventory.quantity_reserved,
                quantity_on_hand_after=inventory.quantity_on_hand,
                quantity_reserved_after=inventory.quantity_reserved,
                reference_type="migration",
                note="Opening balance imported when stock movement history was enabled.",
            )
            for inventory in BranchInventory.objects.all()
        ]
    )


class Migration(migrations.Migration):
    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("inventory", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="StockMovement",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("movement_type", models.CharField(choices=[("opening", "Opening balance"), ("adjustment", "Stock adjustment"), ("reservation", "Stock reserved"), ("release", "Reservation released"), ("sale", "Sale"), ("return", "Customer return"), ("transfer_in", "Transfer in"), ("transfer_out", "Transfer out")], max_length=30)),
                ("quantity_on_hand_change", models.IntegerField(default=0)),
                ("quantity_reserved_change", models.IntegerField(default=0)),
                ("quantity_on_hand_after", models.PositiveIntegerField()),
                ("quantity_reserved_after", models.PositiveIntegerField()),
                ("reference_type", models.CharField(blank=True, max_length=50)),
                ("reference_id", models.CharField(blank=True, max_length=100)),
                ("note", models.CharField(blank=True, max_length=300)),
                ("inventory", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="movements", to="inventory.branchinventory")),
                ("performed_by", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="performed_stock_movements", to=settings.AUTH_USER_MODEL)),
            ],
            options={"ordering": ["-created_at", "-id"]},
        ),
        migrations.AddIndex(
            model_name="stockmovement",
            index=models.Index(fields=["inventory", "created_at"], name="stock_move_inventory_time_idx"),
        ),
        migrations.RunPython(create_opening_movements, migrations.RunPython.noop),
    ]
