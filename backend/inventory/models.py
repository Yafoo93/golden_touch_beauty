from django.db import models

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
        ]

    @property
    def quantity_available(self):
        return self.quantity_on_hand - self.quantity_reserved

    def __str__(self):
        return f"{self.product_variant} at {self.branch}"
