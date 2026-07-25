from django.contrib import admin

from .models import BranchInventory, StockMovement


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


@admin.register(StockMovement)
class StockMovementAdmin(admin.ModelAdmin):
    list_display = (
        "created_at",
        "inventory",
        "movement_type",
        "quantity_on_hand_change",
        "quantity_reserved_change",
        "performed_by",
    )
    list_filter = ("movement_type", "inventory__branch")
    search_fields = (
        "inventory__product_variant__sku",
        "inventory__product_variant__product__name",
        "reference_id",
        "note",
    )
    readonly_fields = (
        "id",
        "inventory",
        "movement_type",
        "quantity_on_hand_change",
        "quantity_reserved_change",
        "quantity_on_hand_after",
        "quantity_reserved_after",
        "reference_type",
        "reference_id",
        "note",
        "performed_by",
        "created_at",
        "updated_at",
    )

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
