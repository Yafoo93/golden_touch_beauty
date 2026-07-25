from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("services", "0002_service_is_featured"),
    ]

    operations = [
        migrations.AddField(
            model_name="service",
            name="image",
            field=models.ImageField(blank=True, upload_to="services/%Y/%m/"),
        ),
    ]
