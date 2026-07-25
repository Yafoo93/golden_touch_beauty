from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError

from core.models import BaseModel


class BranchInventory(BaseModel):
    branch = models.ForeignKey(
        "branches.Branch",
        on_delete=models.PROTECT,
        related_name="inventory",
    )
    product_variant = models.ForeignKey(
        "products.ProductVariant",
        on_delete=models.PROTECT,
        related_name="branch_inventory",
    )
    quantity_on_hand = models.PositiveIntegerField(default=0)
    quantity_reserved = models.PositiveIntegerField(default=0)
    reorder_level = models.PositiveIntegerField(default=5)
    is_available = models.BooleanField(default=True)

    class Meta:
        ordering = ["branch__name", "product_variant__product__name"]
        verbose_name_plural = "branch inventories"
        constraints = [
            models.UniqueConstraint(
                fields=["branch", "product_variant"],
                name="unique_branch_product_inventory",
            ),
            models.CheckConstraint(
                condition=models.Q(quantity_reserved__lte=models.F("quantity_on_hand")),
                name="reserved_stock_not_above_on_hand",
            ),
            models.CheckConstraint(
                condition=models.Q(quantity_on_hand__gte=0),
                name="inventory_on_hand_not_negative",
            ),
            models.CheckConstraint(
                condition=models.Q(quantity_reserved__gte=0),
                name="inventory_reserved_not_negative",
            ),
            models.CheckConstraint(
                condition=models.Q(reorder_level__gte=0),
                name="inventory_reorder_level_not_negative",
            ),
        ]

    @property
    def quantity_available(self):
        return self.quantity_on_hand - self.quantity_reserved

    def __str__(self):
        return f"{self.product_variant} at {self.branch}"


class AppendOnlyStockMovementQuerySet(models.QuerySet):
    def update(self, **kwargs):
        raise ValidationError("Stock movements are append-only and cannot be updated.")

    def delete(self):
        raise ValidationError("Stock movements are append-only and cannot be deleted.")

    def bulk_update(self, objs, fields, batch_size=None):
        raise ValidationError("Stock movements are append-only and cannot be updated.")


class StockMovement(BaseModel):
    class MovementType(models.TextChoices):
        OPENING = "opening", "Opening balance"
        ADJUSTMENT = "adjustment", "Stock adjustment"
        RESERVATION = "reservation", "Stock reserved"
        RELEASE = "release", "Reservation released"
        SALE = "sale", "Sale"
        RETURN = "return", "Customer return"
        TRANSFER_IN = "transfer_in", "Transfer in"
        TRANSFER_OUT = "transfer_out", "Transfer out"

    inventory = models.ForeignKey(
        BranchInventory,
        on_delete=models.PROTECT,
        related_name="movements",
    )
    movement_type = models.CharField(max_length=30, choices=MovementType.choices)
    quantity_on_hand_change = models.IntegerField(default=0)
    quantity_reserved_change = models.IntegerField(default=0)
    quantity_on_hand_after = models.PositiveIntegerField()
    quantity_reserved_after = models.PositiveIntegerField()
    reference_type = models.CharField(max_length=50, blank=True)
    reference_id = models.CharField(max_length=100, blank=True)
    note = models.CharField(max_length=300, blank=True)
    performed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="performed_stock_movements",
    )
    objects = AppendOnlyStockMovementQuerySet.as_manager()

    class Meta:
        ordering = ["-created_at", "-id"]
        indexes = [
            models.Index(
                fields=["inventory", "created_at"],
                name="stock_move_inventory_time_idx",
            )
        ]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(quantity_on_hand_after__gte=0),
                name="stock_movement_on_hand_after_not_negative",
            ),
            models.CheckConstraint(
                condition=models.Q(quantity_reserved_after__gte=0),
                name="stock_movement_reserved_after_not_negative",
            ),
            models.CheckConstraint(
                condition=models.Q(
                    quantity_reserved_after__lte=models.F(
                        "quantity_on_hand_after"
                    )
                ),
                name="stock_movement_reserved_not_above_on_hand",
            ),
        ]

    def __str__(self):
        return f"{self.get_movement_type_display()} for {self.inventory}"

    def save(self, *args, **kwargs):
        if not self._state.adding:
            raise ValidationError(
                "Stock movements are append-only and cannot be updated."
            )
        return super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise ValidationError("Stock movements are append-only and cannot be deleted.")
