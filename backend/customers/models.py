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

    def __str__(self):
        return f"Consent preferences for {self.user}"
