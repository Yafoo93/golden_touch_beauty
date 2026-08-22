import secrets
import uuid
from decimal import Decimal

from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models
from django.utils import timezone

from core.models import ActorTrackedModel, BaseModel, BranchScopedModel


def order_reference():
    return f"GTO-{timezone.localdate():%y%m%d}-{secrets.token_hex(3).upper()}"


class Order(BaseModel, BranchScopedModel, ActorTrackedModel):
    class Status(models.TextChoices):
        AWAITING_PAYMENT = "awaiting_payment", "Awaiting payment"
        PAYMENT_UNDER_REVIEW = "payment_under_review", "Payment under review"
        PAID = "paid", "Paid"
        PROCESSING = "processing", "Processing"
        READY_FOR_PICKUP = "ready_for_pickup", "Ready for pickup"
        SHIPPED = "shipped", "Shipped"
        DELIVERED = "delivered", "Delivered"
        CANCELLED = "cancelled", "Cancelled"
        RETURNED = "returned", "Returned"
        REFUNDED = "refunded", "Refunded"

    class FulfillmentMethod(models.TextChoices):
        PICKUP = "pickup", "Clinic pickup"
        DELIVERY = "delivery", "Delivery"

    reference = models.CharField(
        max_length=24, unique=True, default=order_reference, editable=False
    )
    client_request_id = models.UUIDField(unique=True, default=uuid.uuid4)
    customer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="orders",
        null=True,
        blank=True,
    )
    status = models.CharField(
        max_length=30, choices=Status.choices, default=Status.AWAITING_PAYMENT
    )
    fulfillment_method = models.CharField(
        max_length=20,
        choices=FulfillmentMethod.choices,
        default=FulfillmentMethod.PICKUP,
    )
    currency = models.CharField(max_length=3, default="GHS")
    subtotal = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal("0.00"),
        validators=[MinValueValidator(Decimal("0.00"))],
    )
    delivery_fee = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal("0.00"),
        validators=[MinValueValidator(Decimal("0.00"))],
    )
    total_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal("0.00"),
        validators=[MinValueValidator(Decimal("0.00"))],
    )
    recipient_name = models.CharField(max_length=200, blank=True)
    recipient_phone = models.CharField(max_length=30, blank=True)
    delivery_address = models.TextField(blank=True)
    delivery_city = models.CharField(max_length=120, blank=True)
    delivery_notes = models.TextField(blank=True)
    payment_status = models.CharField(max_length=30, default="pending")
    reservation_expires_at = models.DateTimeField(null=True, blank=True)
    paid_at = models.DateTimeField(null=True, blank=True)
    cancelled_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["customer", "status"]),
            models.Index(fields=["branch", "status"]),
        ]

    def __str__(self):
        return f"{self.reference} at {self.branch}"


class OrderItem(BaseModel):
    order = models.ForeignKey(
        Order, on_delete=models.CASCADE, related_name="items"
    )
    product_variant = models.ForeignKey(
        "products.ProductVariant",
        on_delete=models.PROTECT,
        related_name="order_items",
    )
    product_name = models.CharField(max_length=180)
    product_slug = models.SlugField(max_length=200)
    variant_name = models.CharField(max_length=120)
    sku = models.CharField(max_length=80)
    image_path = models.CharField(max_length=500, blank=True)
    unit_price = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.00"))],
    )
    unit_cost = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal("0.00"),
        validators=[MinValueValidator(Decimal("0.00"))],
    )
    quantity = models.PositiveIntegerField()
    line_total = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.00"))],
    )
    line_cost = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal("0.00"),
        validators=[MinValueValidator(Decimal("0.00"))],
    )
    is_preorder = models.BooleanField(default=False)

    class Meta:
        ordering = ["created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["order", "product_variant"],
                name="unique_order_product_variant",
            )
        ]

    def __str__(self):
        return f"{self.product_name} x{self.quantity} on {self.order.reference}"


class StockReservation(BaseModel):
    class Status(models.TextChoices):
        ACTIVE = "active", "Active"
        CONVERTED = "converted", "Converted to sale"
        RELEASED = "released", "Released"
        EXPIRED = "expired", "Expired"

    order = models.ForeignKey(
        Order, on_delete=models.CASCADE, related_name="stock_reservations"
    )
    order_item = models.OneToOneField(
        OrderItem, on_delete=models.CASCADE, related_name="stock_reservation"
    )
    inventory = models.ForeignKey(
        "inventory.BranchInventory",
        on_delete=models.PROTECT,
        related_name="stock_reservations",
    )
    quantity = models.PositiveIntegerField()
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.ACTIVE
    )
    expires_at = models.DateTimeField()
    released_at = models.DateTimeField(null=True, blank=True)
    converted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["expires_at"]
        indexes = [models.Index(fields=["status", "expires_at"])]

    def __str__(self):
        return f"{self.quantity} reserved for {self.order.reference}"
