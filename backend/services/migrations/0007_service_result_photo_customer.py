from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("accounts", "0003_normalize_existing_phone_numbers"),
        ("services", "0006_service_result_images_and_starting_prices"),
    ]
    operations = [
        migrations.AddField(
            model_name="service",
            name="result_photo_customer",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="published_service_results",
                to="accounts.user",
            ),
        )
    ]
