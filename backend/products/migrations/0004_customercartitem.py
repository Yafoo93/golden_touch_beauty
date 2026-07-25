import django.core.validators
import django.db.models.deletion
import uuid
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("products", "0003_product_image"),
    ]

    operations = [
        migrations.CreateModel(
            name="CustomerCartItem",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("quantity", models.PositiveSmallIntegerField(validators=[django.core.validators.MinValueValidator(1)])),
                ("customer", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="cart_items", to=settings.AUTH_USER_MODEL)),
                ("variant", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="customer_cart_items", to="products.productvariant")),
            ],
            options={"ordering": ["created_at"]},
        ),
        migrations.AddConstraint(
            model_name="customercartitem",
            constraint=models.UniqueConstraint(fields=("customer", "variant"), name="unique_customer_cart_variant"),
        ),
        migrations.AddConstraint(
            model_name="customercartitem",
            constraint=models.CheckConstraint(condition=models.Q(("quantity__gte", 1), ("quantity__lte", 20)), name="customer_cart_quantity_1_to_20"),
        ),
    ]
