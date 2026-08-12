from django.conf import settings
from django.db import models
from django.utils import timezone

from core.models import BaseModel


class Notification(BaseModel):
    class Category(models.TextChoices):
        BOOKING = "booking", "Booking"
        ORDER = "order", "Order"
        PAYMENT = "payment", "Payment"
        SYSTEM = "system", "System"

    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="notifications",
    )
    category = models.CharField(
        max_length=20,
        choices=Category.choices,
        default=Category.SYSTEM,
    )
    title = models.CharField(max_length=180)
    message = models.TextField()
    action_url = models.CharField(max_length=500, blank=True)
    event_key = models.CharField(max_length=255, unique=True)
    read_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["recipient", "read_at", "created_at"])]

    @property
    def is_read(self):
        return self.read_at is not None

    def mark_read(self):
        if self.read_at is None:
            self.read_at = timezone.now()
            self.save(update_fields=["read_at", "updated_at"])

    def __str__(self):
        return f"{self.title} for {self.recipient}"


class EmailJob(BaseModel):
    """Durable queue record processed outside the web request."""

    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        PROCESSING = "processing", "Processing"
        COMPLETED = "completed", "Completed"
        FAILED = "failed", "Failed"

    job_type = models.CharField(max_length=60)
    object_id = models.UUIDField(null=True, blank=True)
    event = models.CharField(max_length=80, blank=True)
    payload = models.JSONField(default=dict, blank=True)
    unique_key = models.CharField(max_length=255, unique=True)
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.PENDING
    )
    attempts = models.PositiveSmallIntegerField(default=0)
    max_attempts = models.PositiveSmallIntegerField(default=5)
    next_attempt_at = models.DateTimeField(default=timezone.now)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    last_error = models.TextField(blank=True)

    class Meta:
        ordering = ["next_attempt_at", "created_at"]
        indexes = [models.Index(fields=["status", "next_attempt_at"])]

    def __str__(self):
        return f"{self.job_type} ({self.get_status_display()})"
