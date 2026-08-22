from decimal import Decimal

from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models

from core.models import BaseModel
from core.storage import public_media_storage


class ProductCategory(BaseModel):
    name = models.CharField(max_length=150, unique=True)
    slug = models.SlugField(max_length=170, unique=True)
    description = models.TextField(blank=True)
    display_order = models.PositiveSmallIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["display_order", "name"]
        verbose_name_plural = "product categories"

    def __str__(self):
        return self.name


class Product(BaseModel):
    class PriceType(models.TextChoices):
        FIXED = "fixed", "Fixed price"
        CONTACT = "contact", "Contact for price"

    category = models.ForeignKey(
        ProductCategory,
        on_delete=models.PROTECT,
        related_name="products",
    )
    name = models.CharField(max_length=180, unique=True)
    slug = models.SlugField(max_length=200, unique=True)
    brand = models.CharField(max_length=150, blank=True)
    description = models.TextField()
    price_type = models.CharField(
        max_length=20,
        choices=PriceType.choices,
        default=PriceType.FIXED,
    )
    image = models.ImageField(
        upload_to="products/%Y/%m/",
        storage=public_media_storage,
        blank=True,
    )
    image_path = models.CharField(max_length=255, blank=True)
    is_featured = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    is_published = models.BooleanField(default=False)

    class Meta:
        ordering = ["category__display_order", "name"]

    def __str__(self):
        return self.name


class WishlistItem(BaseModel):
    customer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="wishlist_items",
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name="wishlist_items",
    )

    class Meta:
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["customer", "product"],
                name="unique_customer_wishlist_product",
            )
        ]

    def __str__(self):
        return f"{self.customer} saved {self.product}"


class CustomerCartItem(BaseModel):
    customer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="cart_items",
    )
    variant = models.ForeignKey(
        "products.ProductVariant",
        on_delete=models.PROTECT,
        related_name="customer_cart_items",
    )
    quantity = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1)],
    )

    class Meta:
        ordering = ["created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["customer", "variant"],
                name="unique_customer_cart_variant",
            ),
            models.CheckConstraint(
                condition=models.Q(quantity__gte=1, quantity__lte=20),
                name="customer_cart_quantity_1_to_20",
            ),
        ]

    def __str__(self):
        return f"{self.customer} cart: {self.variant} x{self.quantity}"


class ProductVariant(BaseModel):
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name="variants",
    )
    name = models.CharField(max_length=120, default="Standard")
    sku = models.CharField(max_length=80, unique=True)
    selling_price = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.00"))],
    )
    cost_price = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.00"))],
    )
    is_preorder = models.BooleanField(default=False)
    estimated_availability_date = models.DateField(null=True, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["product__name", "name"]
        constraints = [
            models.UniqueConstraint(
                fields=["product", "name"],
                name="unique_product_variant_name",
            )
        ]

    def __str__(self):
        return f"{self.product} — {self.name}"
