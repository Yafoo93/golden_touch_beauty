import uuid

from django.conf import settings
from django.db import models
from django.utils import timezone


class BaseModel(models.Model):
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class BranchScopedModel(models.Model):
    """Base for records that belong to one operating branch."""

    branch = models.ForeignKey(
        "branches.Branch",
        on_delete=models.PROTECT,
        related_name="%(app_label)s_%(class)s_records",
    )

    class Meta:
        abstract = True


class ActorTrackedModel(models.Model):
    """Capture who created and most recently changed an operational record."""

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="created_%(app_label)s_%(class)s_records",
    )
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="updated_%(app_label)s_%(class)s_records",
    )

    class Meta:
        abstract = True


class IdempotencyRecord(BaseModel):
    """Persist request outcomes so financial mutations can be retried safely."""

    scope = models.CharField(max_length=100)
    key = models.CharField(max_length=255)
    request_hash = models.CharField(max_length=64)
    response_status = models.PositiveSmallIntegerField(null=True, blank=True)
    response_body = models.JSONField(default=dict, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    expires_at = models.DateTimeField()

    class Meta:
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["scope", "key"],
                name="unique_idempotency_key_per_scope",
            )
        ]
        indexes = [
            models.Index(fields=["scope", "created_at"]),
            models.Index(fields=["expires_at"]),
        ]

    def __str__(self):
        return f"{self.scope}:{self.key}"


class WebsiteContent(BaseModel):
    """An approved, plain-text website field editable by the business owner."""

    key = models.SlugField(max_length=120, unique=True)
    page = models.CharField(max_length=50, db_index=True)
    section = models.CharField(max_length=80)
    label = models.CharField(max_length=150)
    value = models.TextField()
    is_published = models.BooleanField(default=True)
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="updated_website_content",
    )

    class Meta:
        ordering = ["page", "section", "label"]
        verbose_name = "website content"
        verbose_name_plural = "website content"

    def __str__(self):
        return f"{self.page}: {self.label}"


class GalleryItem(BaseModel):
    class DisplaySize(models.TextChoices):
        STANDARD = "standard", "Standard"
        WIDE = "wide", "Wide"
        TALL = "tall", "Tall"

    title = models.CharField(max_length=150)
    category = models.CharField(max_length=120)
    alt_text = models.CharField(max_length=250)
    image = models.ImageField(upload_to="gallery/%Y/%m/", blank=True)
    image_path = models.CharField(max_length=255, blank=True)
    display_size = models.CharField(
        max_length=20,
        choices=DisplaySize.choices,
        default=DisplaySize.STANDARD,
    )
    display_order = models.PositiveSmallIntegerField(default=0)
    is_published = models.BooleanField(default=False)
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="updated_gallery_items",
    )

    class Meta:
        ordering = ["display_order", "created_at"]

    def __str__(self):
        return self.title


class Testimonial(BaseModel):
    class ModerationStatus(models.TextChoices):
        PENDING = "pending", "Pending review"
        APPROVED = "approved", "Approved"
        REJECTED = "rejected", "Rejected"

    class SourceType(models.TextChoices):
        WRITTEN = "written", "Written testimonial"
        VIDEO = "video", "Video transcript"
        DEVELOPMENT_SAMPLE = "development_sample", "Development sample"

    client_name = models.CharField(max_length=150)
    client_attribution = models.CharField(max_length=180, blank=True)
    service_context = models.CharField(max_length=180, blank=True)
    quote = models.TextField()
    source_type = models.CharField(
        max_length=30,
        choices=SourceType.choices,
        default=SourceType.WRITTEN,
    )
    consent_confirmed = models.BooleanField(default=False)
    moderation_status = models.CharField(
        max_length=20,
        choices=ModerationStatus.choices,
        default=ModerationStatus.PENDING,
    )
    is_visible = models.BooleanField(default=False)
    is_featured = models.BooleanField(default=False)
    display_order = models.PositiveSmallIntegerField(default=0)
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="reviewed_testimonials",
    )
    reviewed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["display_order", "-created_at"]

    def mark_reviewed(self, user):
        self.reviewed_by = user
        self.reviewed_at = timezone.now()

    def __str__(self):
        return f"{self.client_name}: {self.service_context or 'Testimonial'}"
