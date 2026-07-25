from rest_framework import serializers

from .models import BranchInventory, StockMovement


class ManagementInventorySerializer(serializers.ModelSerializer):
    branch_id = serializers.UUIDField(source="branch.id", read_only=True)
    branch_code = serializers.CharField(source="branch.code", read_only=True)
    branch_name = serializers.CharField(source="branch.name", read_only=True)
    branch_is_active = serializers.BooleanField(
        source="branch.is_active", read_only=True
    )
    variant_id = serializers.UUIDField(source="product_variant.id", read_only=True)
    variant_name = serializers.CharField(
        source="product_variant.name", read_only=True
    )
    sku = serializers.CharField(source="product_variant.sku", read_only=True)
    variant_is_active = serializers.BooleanField(
        source="product_variant.is_active", read_only=True
    )
    product_id = serializers.UUIDField(
        source="product_variant.product.id", read_only=True
    )
    product_name = serializers.CharField(
        source="product_variant.product.name", read_only=True
    )
    product_slug = serializers.CharField(
        source="product_variant.product.slug", read_only=True
    )
    category_name = serializers.CharField(
        source="product_variant.product.category.name", read_only=True
    )
    selling_price = serializers.DecimalField(
        source="product_variant.selling_price",
        max_digits=12,
        decimal_places=2,
        read_only=True,
    )
    quantity_available = serializers.IntegerField(read_only=True)
    is_low_stock = serializers.SerializerMethodField()

    class Meta:
        model = BranchInventory
        fields = (
            "id",
            "branch_id",
            "branch_code",
            "branch_name",
            "branch_is_active",
            "product_id",
            "product_name",
            "product_slug",
            "category_name",
            "variant_id",
            "variant_name",
            "sku",
            "variant_is_active",
            "selling_price",
            "quantity_on_hand",
            "quantity_reserved",
            "quantity_available",
            "reorder_level",
            "is_available",
            "is_low_stock",
            "updated_at",
        )

    def get_is_low_stock(self, inventory):
        return inventory.quantity_available <= inventory.reorder_level


class StockMovementSerializer(serializers.ModelSerializer):
    branch_id = serializers.UUIDField(source="inventory.branch.id", read_only=True)
    branch_code = serializers.CharField(
        source="inventory.branch.code", read_only=True
    )
    branch_name = serializers.CharField(
        source="inventory.branch.name", read_only=True
    )
    movement_label = serializers.CharField(
        source="get_movement_type_display", read_only=True
    )
    performed_by_name = serializers.SerializerMethodField()

    class Meta:
        model = StockMovement
        fields = (
            "id",
            "branch_id",
            "branch_code",
            "branch_name",
            "movement_type",
            "movement_label",
            "quantity_on_hand_change",
            "quantity_reserved_change",
            "quantity_on_hand_after",
            "quantity_reserved_after",
            "reference_type",
            "reference_id",
            "note",
            "performed_by_name",
            "created_at",
        )

    def get_performed_by_name(self, movement):
        if not movement.performed_by:
            return "System"
        return movement.performed_by.full_name or movement.performed_by.email


class StockAdjustmentInputSerializer(serializers.Serializer):
    branch_id = serializers.UUIDField()
    variant_id = serializers.UUIDField()
    quantity_change = serializers.IntegerField(min_value=-1_000_000, max_value=1_000_000)
    reason = serializers.CharField(max_length=300)

    def validate_quantity_change(self, value):
        if value == 0:
            raise serializers.ValidationError("Enter a non-zero stock change.")
        return value

    def validate_reason(self, value):
        value = value.strip()
        if len(value) < 3:
            raise serializers.ValidationError(
                "Explain why this stock adjustment is required."
            )
        return value
