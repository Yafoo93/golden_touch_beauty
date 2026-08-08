import secrets
from decimal import Decimal

from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models
from django.utils import timezone

from core.models import BaseModel, BranchScopedModel


def payment_reference():
    return f"GTP-{timezone.localdate():%y%m%d}-{secrets.token_hex(3).upper()}"


def receipt_reference():
    return f"GTR-{timezone.localdate():%y%m%d}-{secrets.token_hex(3).upper()}"


class Payment(BaseModel, BranchScopedModel):
    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        SUCCEEDED = "succeeded", "Succeeded"
        FAILED = "failed", "Failed"
        CANCELLED = "cancelled", "Cancelled"
        REFUNDED = "refunded", "Refunded"

    reference = models.CharField(
        max_length=24, unique=True, default=payment_reference, editable=False
    )
    customer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="payments",
        null=True,
        blank=True,
    )
    booking = models.ForeignKey(
        "bookings.Booking",
        on_delete=models.PROTECT,
        related_name="payments",
        null=True,
        blank=True,
    )
    order = models.ForeignKey(
        "orders.Order",
        on_delete=models.PROTECT,
        related_name="payments",
        null=True,
        blank=True,
    )
    provider = models.CharField(max_length=40, default="paystack")
    provider_reference = models.CharField(
        max_length=150, unique=True, null=True, blank=True
    )
    method = models.CharField(max_length=40, blank=True)
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.PENDING
    )
    currency = models.CharField(max_length=3, default="GHS")
    amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.00"))],
    )
    paid_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(
                fields=["customer", "status"],
                name="payments_pa_custome_737a31_idx",
            ),
            models.Index(
                fields=["branch", "status"],
                name="payments_pa_branch__ef106d_idx",
            ),
        ]

    def __str__(self):
        return f"{self.reference} ({self.get_status_display()})"


class Receipt(BaseModel, BranchScopedModel):
    """Immutable customer-facing snapshot issued for one verified payment."""

    reference = models.CharField(
        max_length=24, unique=True, default=receipt_reference, editable=False
    )
    payment = models.OneToOneField(
        Payment, on_delete=models.PROTECT, related_name="receipt"
    )
    customer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="receipts",
    )
    source_type = models.CharField(max_length=20)
    source_reference = models.CharField(max_length=24)
    recipient_name = models.CharField(max_length=200)
    recipient_email = models.EmailField()
    currency = models.CharField(max_length=3, default="GHS")
    amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.00"))],
    )
    line_items = models.JSONField(default=list)
    issued_at = models.DateTimeField(default=timezone.now)
    email_sent_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-issued_at"]
        indexes = [
            models.Index(
                fields=["customer", "issued_at"],
                name="payments_re_custome_258f63_idx",
            ),
            models.Index(
                fields=["branch", "issued_at"],
                name="payments_re_branch__129189_idx",
            ),
        ]

    def __str__(self):
        return f"{self.reference} from {self.branch}"
