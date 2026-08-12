from django.conf import settings
from django.db import models

from core.models import BaseModel


class CustomerConsent(BaseModel):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="customer_consent",
    )
    terms_version = models.CharField(max_length=30)
    privacy_version = models.CharField(max_length=30)
    terms_privacy_accepted_at = models.DateTimeField()
    marketing_consent = models.BooleanField(default=False)
    marketing_consent_updated_at = models.DateTimeField()
    photograph_consent = models.BooleanField(default=False)
    photograph_consent_updated_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Consent preferences for {self.user}"


class CustomerAddress(BaseModel):
    class AddressType(models.TextChoices):
        BILLING = "billing", "Billing"
        DELIVERY = "delivery", "Delivery"
        BOTH = "both", "Billing and delivery"

    customer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="saved_addresses")
    label = models.CharField(max_length=80)
    address_type = models.CharField(max_length=20, choices=AddressType.choices, default=AddressType.DELIVERY)
    recipient_name = models.CharField(max_length=200)
    recipient_phone = models.CharField(max_length=20)
    address_line_1 = models.CharField(max_length=250)
    address_line_2 = models.CharField(max_length=250, blank=True)
    city = models.CharField(max_length=120)
    region = models.CharField(max_length=120)
    landmark = models.CharField(max_length=250, blank=True)
    country = models.CharField(max_length=80, default="Ghana")
    is_default_billing = models.BooleanField(default=False)
    is_default_delivery = models.BooleanField(default=False)

    class Meta:
        ordering = ["-is_default_delivery", "-is_default_billing", "label"]
        constraints = [
            models.UniqueConstraint(fields=["customer"], condition=models.Q(is_default_billing=True), name="one_default_billing_address_per_customer"),
            models.UniqueConstraint(fields=["customer"], condition=models.Q(is_default_delivery=True), name="one_default_delivery_address_per_customer"),
        ]

    def __str__(self):
        return f"{self.label} for {self.customer}"
