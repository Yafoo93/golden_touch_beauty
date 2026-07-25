from django.db import transaction
from django.db.models import F, Q
from rest_framework import generics, status
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404

from branches.models import BranchStaffAssignment
from branches.permissions import (
    BranchAccessQuerysetMixin,
    IsOwnerOrAssignedBranchStaff,
    get_accessible_branch_ids,
)
from products.models import ProductVariant

from .models import BranchInventory, StockMovement
from .serializers import (
    ManagementInventorySerializer,
    StockAdjustmentInputSerializer,
    StockMovementSerializer,
)


class ManagementInventoryListView(
    BranchAccessQuerysetMixin, generics.ListAPIView
):
    serializer_class = ManagementInventorySerializer
    permission_classes = [IsOwnerOrAssignedBranchStaff]
    pagination_class = None
    required_branch_roles = (
        BranchStaffAssignment.Role.MANAGER,
        BranchStaffAssignment.Role.STOCK_MANAGER,
    )
    queryset = BranchInventory.objects.select_related(
        "branch",
        "product_variant",
        "product_variant__product",
        "product_variant__product__category",
    ).order_by("branch__name", "product_variant__product__name", "product_variant__name")

    def get_queryset(self):
        queryset = super().get_queryset()
        branch_id = self.request.query_params.get("branch", "").strip()
        search = self.request.query_params.get("search", "").strip()
        low_stock = self.request.query_params.get("low_stock", "").strip().lower()
        if branch_id:
            queryset = queryset.filter(branch_id=branch_id)
        if search:
            queryset = queryset.filter(
                Q(product_variant__product__name__icontains=search)
                | Q(product_variant__name__icontains=search)
                | Q(product_variant__sku__icontains=search)
                | Q(product_variant__product__category__name__icontains=search)
            )
        if low_stock in {"1", "true", "yes"}:
            queryset = queryset.filter(
                quantity_on_hand__lte=F("quantity_reserved") + F("reorder_level")
            )
        return queryset


class ManagementVariantStockHistoryView(APIView):
    permission_classes = [IsOwnerOrAssignedBranchStaff]
    required_branch_roles = (
        BranchStaffAssignment.Role.MANAGER,
        BranchStaffAssignment.Role.STOCK_MANAGER,
    )

    def get(self, request, variant_id):
        branch_ids = get_accessible_branch_ids(
            request.user, self.required_branch_roles
        )
        variant = get_object_or_404(
            ProductVariant.objects.select_related(
                "product", "product__category"
            ).filter(branch_inventory__branch_id__in=branch_ids).distinct(),
            id=variant_id,
        )
        inventories = BranchInventory.objects.select_related("branch").filter(
            product_variant=variant,
            branch_id__in=branch_ids,
        )
        movements = StockMovement.objects.select_related(
            "inventory__branch", "performed_by"
        ).filter(
            inventory__product_variant=variant,
            inventory__branch_id__in=branch_ids,
        )
        return Response(
            {
                "variant": {
                    "id": str(variant.id),
                    "product_name": variant.product.name,
                    "product_slug": variant.product.slug,
                    "category_name": variant.product.category.name,
                    "variant_name": variant.name,
                    "sku": variant.sku,
                    "is_active": variant.is_active,
                },
                "current_stock": ManagementInventorySerializer(
                    inventories, many=True
                ).data,
                "movements": StockMovementSerializer(movements, many=True).data,
            }
        )


class ManagementStockAdjustmentView(APIView):
    permission_classes = [IsOwnerOrAssignedBranchStaff]
    required_branch_roles = (
        BranchStaffAssignment.Role.MANAGER,
        BranchStaffAssignment.Role.STOCK_MANAGER,
    )

    @transaction.atomic
    def post(self, request):
        serializer = StockAdjustmentInputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        inventory = (
            BranchInventory.objects.select_for_update()
            .select_related(
                "branch",
                "product_variant",
                "product_variant__product",
                "product_variant__product__category",
            )
            .filter(
                branch_id=data["branch_id"],
                product_variant_id=data["variant_id"],
            )
            .first()
        )
        if inventory is None:
            raise ValidationError(
                {"stock": "No inventory record exists for this variant and branch."}
            )
        new_quantity = inventory.quantity_on_hand + data["quantity_change"]
        if new_quantity < inventory.quantity_reserved:
            raise ValidationError(
                {
                    "quantity_change": (
                        "The resulting stock cannot be below the quantity "
                        "already reserved."
                    )
                }
            )
        inventory.quantity_on_hand = new_quantity
        inventory.save(update_fields=["quantity_on_hand", "updated_at"])
        movement = StockMovement.objects.create(
            inventory=inventory,
            movement_type=StockMovement.MovementType.ADJUSTMENT,
            quantity_on_hand_change=data["quantity_change"],
            quantity_on_hand_after=inventory.quantity_on_hand,
            quantity_reserved_after=inventory.quantity_reserved,
            note=data["reason"],
            performed_by=request.user,
        )
        return Response(
            {
                "inventory": ManagementInventorySerializer(inventory).data,
                "movement": StockMovementSerializer(movement).data,
            },
            status=status.HTTP_201_CREATED,
        )

# Create your views here.
