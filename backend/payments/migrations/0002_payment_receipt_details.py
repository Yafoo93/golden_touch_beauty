import django.db.models.deletion
import django.utils.timezone
from decimal import Decimal
from django.conf import settings
from django.db import migrations, models
import django.core.validators
import payments.models


class Migration(migrations.Migration):
    dependencies = [
        ("accounts", "0003_normalize_existing_phone_numbers"),
        ("bookings", "0003_alter_booking_treatment_photo"),
        ("orders", "0002_orderitem_stockreservation_order_cancelled_at_and_more"),
        ("payments", "0001_initial"),
    ]

    operations = [
        migrations.AddField(model_name="payment", name="amount", field=models.DecimalField(decimal_places=2, default=Decimal("0.00"), max_digits=12)),
        migrations.AddField(model_name="payment", name="booking", field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name="payments", to="bookings.booking")),
        migrations.AddField(model_name="payment", name="currency", field=models.CharField(default="GHS", max_length=3)),
        migrations.AddField(model_name="payment", name="customer", field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name="payments", to=settings.AUTH_USER_MODEL)),
        migrations.AddField(model_name="payment", name="method", field=models.CharField(blank=True, max_length=40)),
        migrations.AddField(model_name="payment", name="order", field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name="payments", to="orders.order")),
        migrations.AddField(model_name="payment", name="paid_at", field=models.DateTimeField(blank=True, null=True)),
        migrations.AddField(model_name="payment", name="provider", field=models.CharField(default="paystack", max_length=40)),
        migrations.AddField(model_name="payment", name="provider_reference", field=models.CharField(blank=True, max_length=150, null=True, unique=True)),
        migrations.AddField(model_name="payment", name="reference", field=models.CharField(default=payments.models.payment_reference, editable=False, max_length=24, unique=True)),
        migrations.AddField(model_name="payment", name="status", field=models.CharField(choices=[("pending", "Pending"), ("succeeded", "Succeeded"), ("failed", "Failed"), ("cancelled", "Cancelled"), ("refunded", "Refunded")], default="pending", max_length=20)),
        migrations.AddField(model_name="receipt", name="amount", field=models.DecimalField(decimal_places=2, default=Decimal("0.00"), max_digits=12)),
        migrations.AddField(model_name="receipt", name="currency", field=models.CharField(default="GHS", max_length=3)),
        migrations.AddField(model_name="receipt", name="customer", field=models.ForeignKey(default=None, on_delete=django.db.models.deletion.PROTECT, related_name="receipts", to=settings.AUTH_USER_MODEL)),
        migrations.AddField(model_name="receipt", name="email_sent_at", field=models.DateTimeField(blank=True, null=True)),
        migrations.AddField(model_name="receipt", name="issued_at", field=models.DateTimeField(default=django.utils.timezone.now)),
        migrations.AddField(model_name="receipt", name="line_items", field=models.JSONField(default=list)),
        migrations.AddField(model_name="receipt", name="payment", field=models.OneToOneField(default=None, on_delete=django.db.models.deletion.PROTECT, related_name="receipt", to="payments.payment")),
        migrations.AddField(model_name="receipt", name="recipient_email", field=models.EmailField(default="", max_length=254)),
        migrations.AddField(model_name="receipt", name="recipient_name", field=models.CharField(default="", max_length=200)),
        migrations.AddField(model_name="receipt", name="reference", field=models.CharField(default=payments.models.receipt_reference, editable=False, max_length=24, unique=True)),
        migrations.AddField(model_name="receipt", name="source_reference", field=models.CharField(default="", max_length=24)),
        migrations.AddField(model_name="receipt", name="source_type", field=models.CharField(default="", max_length=20)),
        migrations.AlterField(model_name="payment", name="amount", field=models.DecimalField(decimal_places=2, max_digits=12, validators=[django.core.validators.MinValueValidator(Decimal("0.00"))])),
        migrations.AlterField(model_name="receipt", name="amount", field=models.DecimalField(decimal_places=2, max_digits=12, validators=[django.core.validators.MinValueValidator(Decimal("0.00"))])),
        migrations.AlterField(model_name="receipt", name="customer", field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="receipts", to=settings.AUTH_USER_MODEL)),
        migrations.AlterField(model_name="receipt", name="payment", field=models.OneToOneField(on_delete=django.db.models.deletion.PROTECT, related_name="receipt", to="payments.payment")),
        migrations.AlterField(model_name="receipt", name="recipient_email", field=models.EmailField(max_length=254)),
        migrations.AlterField(model_name="receipt", name="recipient_name", field=models.CharField(max_length=200)),
        migrations.AlterField(model_name="receipt", name="source_reference", field=models.CharField(max_length=24)),
        migrations.AlterField(model_name="receipt", name="source_type", field=models.CharField(max_length=20)),
        migrations.AlterModelOptions(name="receipt", options={"ordering": ["-issued_at"]}),
        migrations.AddIndex(model_name="payment", index=models.Index(fields=["customer", "status"], name="payments_pa_custome_737a31_idx")),
        migrations.AddIndex(model_name="payment", index=models.Index(fields=["branch", "status"], name="payments_pa_branch__ef106d_idx")),
        migrations.AddIndex(model_name="receipt", index=models.Index(fields=["customer", "issued_at"], name="payments_re_custome_258f63_idx")),
        migrations.AddIndex(model_name="receipt", index=models.Index(fields=["branch", "issued_at"], name="payments_re_branch__129189_idx")),
    ]
