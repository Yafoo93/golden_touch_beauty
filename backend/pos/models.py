import secrets
from decimal import Decimal

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models
from django.utils import timezone

from core.models import BaseModel, BranchScopedModel


def pos_sale_reference():
    return f"GTS-{timezone.localdate():%y%m%d}-{secrets.token_hex(3).upper()}"


def pos_receipt_reference():
    return f"GTR-POS-{timezone.localdate():%y%m%d}-{secrets.token_hex(3).upper()}"


class POSSale(BaseModel, BranchScopedModel):
    class Status(models.TextChoices):
        DRAFT = "draft", "Draft"
        COMPLETED = "completed", "Completed"
        VOIDED = "voided", "Voided"
        REFUNDED = "refunded", "Refunded"

    reference = models.CharField(max_length=24, unique=True, default=pos_sale_reference, editable=False)
    receipt_reference = models.CharField(max_length=28, unique=True, default=pos_receipt_reference, editable=False)
    cashier = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.PROTECT, related_name="pos_sales")
    customer = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.PROTECT, related_name="pos_purchases")
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.DRAFT)
    payment_status = models.CharField(max_length=30, default="pending")
    currency = models.CharField(max_length=3, default="GHS")
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"), validators=[MinValueValidator(Decimal("0.00"))])
    item_count = models.PositiveIntegerField(default=0)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-completed_at", "-created_at"]
        indexes = [
            models.Index(fields=["branch", "status", "created_at"], name="pos_possale_branch_status_idx"),
            models.Index(fields=["cashier", "created_at"], name="pos_possale_cashier_idx"),
        ]

    def __str__(self):
        return f"{self.reference} at {self.branch}"

    def save(self, *args, **kwargs):
        if not self._state.adding:
            original_status = type(self).objects.filter(pk=self.pk).values_list("status", flat=True).first()
            if original_status in (self.Status.COMPLETED, self.Status.VOIDED, self.Status.REFUNDED):
                raise ValidationError(
                    "Finalized POS sales are immutable. Use the authorized reversal or refund workflow."
                )
        if self.status != self.Status.DRAFT and self.cashier_id is None:
            raise ValidationError({"cashier": "A cashier is required for every completed POS sale and receipt."})
        return super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        if self.status in (self.Status.COMPLETED, self.Status.VOIDED, self.Status.REFUNDED):
            raise ValidationError(
                "Finalized POS sales cannot be deleted. Use the authorized reversal or refund workflow."
            )
        return super().delete(*args, **kwargs)


class POSSaleLine(BaseModel):
    class ItemType(models.TextChoices):
        PRODUCT = "product", "Product"
        SERVICE = "service", "Service"

    sale = models.ForeignKey(POSSale, on_delete=models.PROTECT, related_name="lines")
    item_type = models.CharField(max_length=20, choices=ItemType.choices)
    item_reference = models.CharField(max_length=100)
    name = models.CharField(max_length=180)
    option_name = models.CharField(max_length=150, blank=True)
    sku = models.CharField(max_length=80, blank=True)
    quantity = models.PositiveIntegerField()
    unit_price = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(Decimal("0.00"))])
    unit_cost = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"), validators=[MinValueValidator(Decimal("0.00"))])
    line_total = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(Decimal("0.00"))])
    line_cost = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"), validators=[MinValueValidator(Decimal("0.00"))])

    class Meta:
        ordering = ["created_at"]


class POSPaymentEntry(BaseModel):
    sale = models.ForeignKey(POSSale, on_delete=models.PROTECT, related_name="payment_entries")
    method = models.CharField(max_length=40)
    reference = models.CharField(max_length=150, blank=True)
    amount = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(Decimal("0.00"))])
    status = models.CharField(max_length=20, default="succeeded")

    class Meta:
        ordering = ["created_at"]
