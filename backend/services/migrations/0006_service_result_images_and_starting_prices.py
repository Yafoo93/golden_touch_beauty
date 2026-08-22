from django.db import migrations, models
import core.storage


def convert_non_consultations(apps, schema_editor):
    Service = apps.get_model("services", "Service")
    Service.objects.filter(price_type="fixed", is_consultation=False).update(
        price_type="starting_from"
    )


class Migration(migrations.Migration):
    dependencies = [("services", "0005_alter_service_image")]
    operations = [
        migrations.AlterField(
            model_name="service",
            name="price_type",
            field=models.CharField(
                choices=[
                    ("fixed", "Fixed price"),
                    ("starting_from", "Starting from"),
                    ("range", "Price range"),
                    ("options", "Price options"),
                    ("quotation", "Manual quotation"),
                ],
                default="starting_from",
                max_length=30,
            ),
        ),
        migrations.AddField(model_name="service", name="before_image", field=models.ImageField(blank=True, storage=core.storage.private_media_storage, upload_to="services/results/%Y/%m/")),
        migrations.AddField(model_name="service", name="after_image", field=models.ImageField(blank=True, storage=core.storage.private_media_storage, upload_to="services/results/%Y/%m/")),
        migrations.AddField(model_name="service", name="result_photo_consent_confirmed", field=models.BooleanField(default=False)),
        migrations.AddField(model_name="service", name="result_photo_consent_reference", field=models.CharField(blank=True, max_length=120)),
        migrations.AddField(model_name="service", name="result_images_approved", field=models.BooleanField(default=False)),
        migrations.RunPython(convert_non_consultations, migrations.RunPython.noop),
    ]
