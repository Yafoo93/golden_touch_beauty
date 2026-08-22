from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("products", "0005_alter_product_image")]
    operations = [
        migrations.AddField(
            model_name="product",
            name="price_type",
            field=models.CharField(
                choices=[("fixed", "Fixed price"), ("contact", "Contact for price")],
                default="fixed",
                max_length=20,
            ),
        ),
    ]
