from django.conf import settings
from django.core.validators import RegexValidator
from django.db import models

from core.models import BaseModel


class Branch(BaseModel):
    code_validator = RegexValidator(
        regex=r"^[A-Z0-9_-]+$",
        message="Use uppercase letters, numbers, hyphens, or underscores.",
    )

    name = models.CharField(max_length=150, unique=True)
    code = models.CharField(
        max_length=30,
        unique=True,
        validators=[code_validator],
    )
    address = models.TextField()
    telephone_number = models.CharField(max_length=30)
    secondary_telephone_number = models.CharField(max_length=30, blank=True)
    whatsapp_number = models.CharField(max_length=30, blank=True)
    secondary_whatsapp_number = models.CharField(max_length=30, blank=True)
    email = models.EmailField(blank=True)
    google_maps_url = models.URLField(blank=True)
    opening_days = models.JSONField(default=list)
    opening_time = models.TimeField()
    closing_time = models.TimeField()
    assigned_manager = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="managed_branches",
    )
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["name"]
        verbose_name_plural = "branches"

    def save(self, *args, **kwargs):
        self.code = self.code.strip().upper()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.name} ({self.code})"
