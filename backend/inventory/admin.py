from django.contrib import admin

from .models import BranchInventory


@admin.register(BranchInventory)
class BranchInventoryAdmin(admin.ModelAdmin):
    list_display = (
        "product_variant",
        "branch",
        "quantity_on_hand",
        "quantity_reserved",
        "available_quantity",
        "reorder_level",
        "is_available",
    )
    list_filter = ("branch", "is_available")
    search_fields = (
        "product_variant__sku",
        "product_variant__product__name",
        "branch__name",
    )
    readonly_fields = ("id", "quantity_reserved", "created_at", "updated_at")

    @admin.display(description="Available")
    def available_quantity(self, obj):
        return obj.quantity_available
