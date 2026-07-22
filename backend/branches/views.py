from collections import defaultdict

from rest_framework import generics, serializers, status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.models import User
from inventory.models import BranchInventory
from products.models import ProductVariant

from .models import Branch
from .permissions import IsOwner
from .serializers import (
    BranchManagerOptionSerializer,
    ManagementBranchCreateSerializer,
    ManagementBranchSerializer,
    PickupOptionsRequestSerializer,
    PublicBranchSerializer,
)


class PublicBranchListView(generics.ListAPIView):
    serializer_class = PublicBranchSerializer
    permission_classes = [AllowAny]
    queryset = Branch.objects.filter(is_active=True).order_by("name")


class PublicBranchDetailView(generics.RetrieveAPIView):
    serializer_class = PublicBranchSerializer
    permission_classes = [AllowAny]
    queryset = Branch.objects.filter(is_active=True)


class ManagementBranchListView(generics.ListCreateAPIView):
    permission_classes = [IsOwner]
    queryset = Branch.objects.select_related("assigned_manager").order_by("name")

    def get_serializer_class(self):
        if self.request.method == "POST":
            return ManagementBranchCreateSerializer
        return ManagementBranchSerializer


class ManagementBranchDetailView(generics.RetrieveUpdateAPIView):
    permission_classes = [IsOwner]
    queryset = Branch.objects.select_related("assigned_manager")

    def get_serializer_class(self):
        if self.request.method in {"PUT", "PATCH"}:
            return ManagementBranchCreateSerializer
        return ManagementBranchSerializer


class BranchManagerOptionListView(generics.ListAPIView):
    serializer_class = BranchManagerOptionSerializer
    permission_classes = [IsOwner]
    pagination_class = None
    queryset = User.objects.filter(is_active=True, is_staff=True).order_by("full_name")


class PickupBranchOptionsView(APIView):
    # This is a read-only availability calculation that uses POST solely for
    # its structured item payload. It has no user state or data mutation.
    authentication_classes = []
    permission_classes = [AllowAny]

    def post(self, request):
        request_serializer = PickupOptionsRequestSerializer(data=request.data)
        request_serializer.is_valid(raise_exception=True)

        requested = defaultdict(int)
        identifiers = {}
        for item in request_serializer.validated_data["items"]:
            key = (
                ("id", str(item["variant_id"]))
                if item.get("variant_id")
                else ("sku", item["sku"])
            )
            requested[key] += item["quantity"]
            identifiers[key] = item

        variants = {}
        for key in requested:
            lookup = {"id": key[1]} if key[0] == "id" else {"sku": key[1]}
            try:
                variant = ProductVariant.objects.select_related("product").get(
                    **lookup,
                    is_active=True,
                    product__is_active=True,
                    product__is_published=True,
                )
            except ProductVariant.DoesNotExist as exc:
                raise serializers.ValidationError(
                    {"items": [f"Product variant {key[1]} is unavailable."]}
                ) from exc
            variants[key] = variant

        branches = list(Branch.objects.filter(is_active=True).order_by("name"))
        inventory = {
            (row.branch_id, row.product_variant_id): row
            for row in BranchInventory.objects.filter(
                branch__in=branches,
                product_variant__in=variants.values(),
            )
        }

        results = []
        for branch in branches:
            unavailable_items = []
            for key, quantity in requested.items():
                variant = variants[key]
                row = inventory.get((branch.id, variant.id))
                if not row or not row.is_available or row.quantity_available < quantity:
                    unavailable_items.append(
                        {
                            "variant_id": str(variant.id),
                            "sku": variant.sku,
                            "name": str(variant),
                            "reason": "Insufficient stock for pickup.",
                        }
                    )
            results.append(
                {
                    "branch": PublicBranchSerializer(branch).data,
                    "eligible": not unavailable_items,
                    "unavailable_items": unavailable_items,
                }
            )

        return Response({"results": results}, status=status.HTTP_200_OK)
