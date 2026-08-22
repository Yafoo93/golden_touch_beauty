from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("bookings", "0004_alter_booking_treatment_photo")]
    operations = [
        migrations.AddField(
            model_name="booking",
            name="pricing_status",
            field=models.CharField(
                choices=[("final", "Final price"), ("estimate", "Starting-price estimate")],
                default="final",
                max_length=20,
            ),
        )
    ]
