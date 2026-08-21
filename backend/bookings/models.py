import secrets
import uuid
from pathlib import Path
from decimal import Decimal

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models
from django.utils import timezone

from core.models import ActorTrackedModel, BaseModel, BranchScopedModel
from core.storage import private_media_storage


def booking_reference():
    return f"GTB-{timezone.localdate():%y%m%d}-{secrets.token_hex(3).upper()}"


def booking_intake_path(instance, filename):
    extension = Path(filename).suffix.lower()[:10]
    return (
        f"private/booking-intake/{timezone.localdate():%Y/%m}/"
        f"{uuid.uuid4().hex}{extension}"
    )


class Booking(BaseModel, BranchScopedModel, ActorTrackedModel):
    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        CONFIRMED = "confirmed", "Confirmed"
        CHECKED_IN = "checked_in", "Checked in"
        IN_PROGRESS = "in_progress", "In progress"
        COMPLETED = "completed", "Completed"
        CANCELLED = "cancelled", "Cancelled"
        RESCHEDULED = "rescheduled", "Rescheduled"
        NO_SHOW = "no_show", "No-show"
        REJECTED = "rejected", "Rejected"
        PROPOSED = "proposed", "Proposed time"

    class PaymentMethod(models.TextChoices):
        ONLINE = "online", "Pay online"
        CLINIC = "clinic", "Pay at clinic"

    class Source(models.TextChoices):
        WEBSITE = "website", "Website"
        PHONE = "phone", "Phone"
        WHATSAPP = "whatsapp", "WhatsApp"
        WALK_IN = "walk_in", "Walk-in"

    reference = models.CharField(
        max_length=24, unique=True, default=booking_reference, editable=False
    )
    client_request_id = models.UUIDField(unique=True, default=uuid.uuid4)
    customer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="bookings",
        null=True,
        blank=True,
    )
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.PENDING
    )
    source = models.CharField(
        max_length=20, choices=Source.choices, default=Source.WEBSITE
    )
    preferred_start = models.DateTimeField(default=timezone.now)
    proposed_start = models.DateTimeField(null=True, blank=True)
    proposed_expires_at = models.DateTimeField(null=True, blank=True)
    total_duration_minutes = models.PositiveIntegerField(default=0)
    total_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal("0.00"),
        validators=[MinValueValidator(Decimal("0.00"))],
    )
    recipient_is_customer = models.BooleanField(default=True)
    recipient_name = models.CharField(max_length=200, blank=True)
    recipient_phone = models.CharField(max_length=20, blank=True)
    allergies = models.TextField(blank=True)
    conditions = models.TextField(blank=True)
    previous_treatments = models.TextField(blank=True)
    notes = models.TextField(blank=True)
    treatment_photo = models.ImageField(
        upload_to=booking_intake_path,
        storage=private_media_storage,
        blank=True,
    )
    photo_marketing_consent = models.BooleanField(default=False)
    payment_method = models.CharField(
        max_length=20, choices=PaymentMethod.choices, default=PaymentMethod.ONLINE
    )
    payment_status = models.CharField(max_length=20, default="pending")
    duplicate_override = models.BooleanField(default=False)
    duplicate_override_reason = models.CharField(max_length=300, blank=True)

    class Meta:
        ordering = ["preferred_start", "reference"]
        indexes = [
            models.Index(fields=["branch", "preferred_start"]),
            models.Index(fields=["customer", "status"]),
        ]

    def __str__(self):
        return f"{self.reference} at {self.branch}"


class BookingServiceItem(BaseModel):
    booking = models.ForeignKey(
        Booking, on_delete=models.CASCADE, related_name="service_items"
    )
    service = models.ForeignKey(
        "services.Service", on_delete=models.PROTECT, related_name="booking_items"
    )
    price_option = models.ForeignKey(
        "services.ServicePriceOption",
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="booking_items",
    )
    service_name = models.CharField(max_length=180)
    option_name = models.CharField(max_length=150, blank=True)
    unit_price = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.00"))],
    )
    duration_minutes = models.PositiveIntegerField()

    class Meta:
        ordering = ["created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["booking", "service"],
                name="unique_booking_service",
            )
        ]

    def __str__(self):
        return f"{self.service_name} on {self.booking.reference}"


class BookingHistory(BaseModel):
    booking = models.ForeignKey(
        Booking, on_delete=models.CASCADE, related_name="history"
    )
    action = models.CharField(max_length=50)
    from_status = models.CharField(max_length=20, blank=True)
    to_status = models.CharField(max_length=20, blank=True)
    reason = models.TextField(blank=True)
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="booking_history_actions",
    )
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ["created_at"]

    def save(self, *args, **kwargs):
        if not self._state.adding:
            raise ValidationError("Booking history is append-only.")
        return super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise ValidationError("Booking history is append-only.")


class BookingBlock(BaseModel, BranchScopedModel, ActorTrackedModel):
    class BlockType(models.TextChoices):
        HOLIDAY = "holiday", "Holiday"
        MEETING = "meeting", "Meeting"
        EVENT = "event", "Event"
        UNAVAILABLE = "unavailable", "Unavailable"

    starts_at = models.DateTimeField()
    ends_at = models.DateTimeField()
    block_type = models.CharField(
        max_length=20, choices=BlockType.choices, default=BlockType.UNAVAILABLE
    )
    reason = models.CharField(max_length=300)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["starts_at"]
        indexes = [models.Index(fields=["branch", "starts_at", "ends_at"])]

    def clean(self):
        if self.ends_at <= self.starts_at:
            raise ValidationError({"ends_at": "End time must be after start time."})

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)
