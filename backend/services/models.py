from decimal import Decimal

from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from core.models import BaseModel


class ServiceCategory(BaseModel):
    name = models.CharField(max_length=150, unique=True)
    slug = models.SlugField(max_length=170, unique=True)
    description = models.TextField(blank=True)
    display_order = models.PositiveSmallIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["display_order", "name"]
        verbose_name_plural = "service categories"

    def __str__(self):
        return self.name


class Service(BaseModel):
    class PriceType(models.TextChoices):
        FIXED = "fixed", "Fixed price"
        STARTING_FROM = "starting_from", "Starting from"
        RANGE = "range", "Price range"
        OPTIONS = "options", "Price options"
        QUOTATION = "quotation", "Manual quotation"

    category = models.ForeignKey(
        ServiceCategory,
        on_delete=models.PROTECT,
        related_name="services",
    )
    name = models.CharField(max_length=180, unique=True)
    slug = models.SlugField(max_length=200, unique=True)
    short_description = models.CharField(max_length=300)
    description = models.TextField()
    price_type = models.CharField(
        max_length=30,
        choices=PriceType.choices,
        default=PriceType.FIXED,
    )
    price = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.00"))],
    )
    maximum_price = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(Decimal("0.00"))],
    )
    pricing_notes = models.CharField(max_length=300, blank=True)
    duration_minutes = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(1440)]
    )
    image_path = models.CharField(max_length=255, blank=True)
    is_clinic_service = models.BooleanField(default=True)
    is_home_service = models.BooleanField(default=False)
    requires_full_payment = models.BooleanField(default=True)
    allows_pay_at_clinic = models.BooleanField(default=True)
    is_consultation = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    is_published = models.BooleanField(default=False)
    branches = models.ManyToManyField(
        "branches.Branch",
        through="ServiceBranchAvailability",
        related_name="services",
    )

    class Meta:
        ordering = ["category__display_order", "name"]

    def __str__(self):
        return self.name


class ServiceBranchAvailability(BaseModel):
    service = models.ForeignKey(
        Service,
        on_delete=models.CASCADE,
        related_name="branch_availability",
    )
    branch = models.ForeignKey(
        "branches.Branch",
        on_delete=models.CASCADE,
        related_name="service_availability",
    )
    is_available = models.BooleanField(default=True)

    class Meta:
        ordering = ["branch__name", "service__name"]
        constraints = [
            models.UniqueConstraint(
                fields=["service", "branch"],
                name="unique_service_branch_availability",
            )
        ]

    def __str__(self):
        return f"{self.service} at {self.branch}"
