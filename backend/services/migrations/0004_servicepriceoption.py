import uuid
from decimal import Decimal

from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("services", "0003_service_image"),
    ]

    operations = [
        migrations.CreateModel(
            name="ServicePriceOption",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("name", models.CharField(max_length=150)),
                ("description", models.CharField(blank=True, max_length=300)),
                ("price", models.DecimalField(decimal_places=2, max_digits=12, validators=[MinValueValidator(Decimal("0.00"))])),
                ("duration_minutes", models.PositiveSmallIntegerField(blank=True, null=True, validators=[MinValueValidator(1), MaxValueValidator(1440)])),
                ("display_order", models.PositiveSmallIntegerField(default=0)),
                ("is_active", models.BooleanField(default=True)),
                ("service", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="price_options", to="services.service")),
            ],
            options={
                "ordering": ["display_order", "price", "name"],
                "constraints": [models.UniqueConstraint(fields=("service", "name"), name="unique_service_price_option_name")],
            },
        ),
    ]
