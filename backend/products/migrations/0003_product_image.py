from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("products", "0002_wishlistitem")]

    operations = [
        migrations.AddField(
            model_name="product",
            name="image",
            field=models.ImageField(blank=True, upload_to="products/%Y/%m/"),
        ),
    ]
