from django.db import transaction
from django.db.models import Count, Exists, F, OuterRef, Prefetch, Q
from rest_framework import filters, generics, serializers, status
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from inventory.models import BranchInventory
from branches.permissions import IsOwner
from branches.models import Branch
from auditlog.services import actor_role_for, client_device, client_ip, record_event

from .models import CustomerCartItem, Product, ProductCategory, ProductVariant, WishlistItem
from .serializers import (
    CartLineSerializer,
    CartQuantitySerializer,
    CustomerCartItemSerializer,
    FeaturedProductSerializer,
    CartValidationSerializer,
    ManagementProductListSerializer,
    ManagementProductBranchOptionSerializer,
    ManagementProductCategoryOptionSerializer,
    ManagementProductCategorySerializer,
    ManagementProductCreateSerializer,
    ManagementProductDetailSerializer,
    ManagementProductUpdateSerializer,
    PublicProductCategorySerializer,
    PublicProductDetailSerializer,
    PublicProductSerializer,
)


def public_stock():
    return BranchInventory.objects.select_related("branch").filter(
        is_available=True,
        branch__is_active=True,
    )


def validate_cart_lines(lines):
    """Return cart lines rebuilt from live catalogue prices and branch stock."""
    requested = {line["variant_id"]: line["quantity"] for line in lines}
    variants = (
        ProductVariant.objects.select_related("product", "product__category")
        .prefetch_related(Prefetch("branch_inventory", queryset=public_stock()))
        .filter(
            id__in=requested,
            is_active=True,
            product__is_active=True,
            product__is_published=True,
            product__category__is_active=True,
        )
    )
    items = []
    adjustments = []
    found_ids = set()
    for variant in variants:
        found_ids.add(variant.id)
        if variant.product.price_type == Product.PriceType.CONTACT:
            adjustments.append({
                "variant_id": str(variant.id),
                "code": "contact_for_price",
                "message": f"{variant.product.name} requires a price enquiry and cannot be added to cart.",
            })
            continue
        requested_quantity = requested[variant.id]
        maximum_stock = max(
            (stock.quantity_available for stock in variant.branch_inventory.all()),
            default=0,
        )
        allowed_quantity = (
            requested_quantity
            if variant.is_preorder
            else min(requested_quantity, maximum_stock)
        )
        if allowed_quantity < 1:
            adjustments.append(
                {
                    "variant_id": str(variant.id),
                    "code": "out_of_stock",
                    "message": f"{variant.product.name} is currently out of stock and was removed.",
                }
            )
            continue
        if allowed_quantity != requested_quantity:
            adjustments.append(
                {
                    "variant_id": str(variant.id),
                    "code": "quantity_reduced",
                    "message": (
                        f"{variant.product.name} was reduced to {allowed_quantity}, "
                        "the highest quantity currently available at one branch."
                    ),
                }
            )
        product = variant.product
        items.append(
            {
                "variant_id": str(variant.id),
                "sku": variant.sku,
                "product_slug": product.slug,
                "product_name": product.name,
                "variant_name": variant.name,
                "unit_price": str(variant.selling_price),
                "quantity": allowed_quantity,
                "image_src": product.image.url if product.image else product.image_path,
            }
        )
    for variant_id in set(requested) - found_ids:
        adjustments.append(
            {
                "variant_id": str(variant_id),
                "code": "unavailable",
                "message": "A product that is no longer available was removed from your cart.",
            }
        )
    return items, adjustments


def replace_customer_cart(user, items):
    CustomerCartItem.objects.filter(customer=user).delete()
    CustomerCartItem.objects.bulk_create(
        [
            CustomerCartItem(
                customer=user,
                variant_id=item["variant_id"],
                quantity=item["quantity"],
            )
            for item in items
        ]
    )


def public_variants():
    return ProductVariant.objects.filter(is_active=True).prefetch_related(
        Prefetch("branch_inventory", queryset=public_stock())
    )


class FeaturedProductListView(generics.ListAPIView):
    serializer_class = FeaturedProductSerializer
    permission_classes = [AllowAny]
    pagination_class = None

    def get_queryset(self):
        return (
            Product.objects.select_related("category")
            .filter(
                is_featured=True,
                is_active=True,
                is_published=True,
                category__is_active=True,
            )
            .prefetch_related(Prefetch("variants", queryset=public_variants()))
            .order_by("category__display_order", "name")[:8]
        )


class PublicProductListView(generics.ListAPIView):
    serializer_class = PublicProductSerializer
    permission_classes = [AllowAny]
    pagination_class = None
    filter_backends = [filters.OrderingFilter]
    ordering_fields = ("name", "variants__selling_price", "category__name")
    ordering = ("category__display_order", "name")

    def get_queryset(self):
        live_stock = BranchInventory.objects.filter(
            product_variant__product_id=OuterRef("pk"),
            product_variant__is_active=True,
            is_available=True,
            branch__is_active=True,
            quantity_on_hand__gt=F("quantity_reserved"),
        )
        queryset = (
            Product.objects.select_related("category")
            .filter(
                is_active=True,
                is_published=True,
                category__is_active=True,
                variants__is_active=True,
            )
            .annotate(has_live_stock=Exists(live_stock))
            .prefetch_related(Prefetch("variants", queryset=public_variants()))
            .distinct()
        )
        category = self.request.query_params.get("category", "").strip()
        search = self.request.query_params.get("search", "").strip()
        availability = self.request.query_params.get("availability", "").strip()
        if category:
            queryset = queryset.filter(category__slug=category)
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search)
                | Q(brand__icontains=search)
                | Q(description__icontains=search)
                | Q(category__name__icontains=search)
            )
        if availability == "in_stock":
            queryset = queryset.filter(has_live_stock=True)
        elif availability == "preorder":
            queryset = queryset.filter(
                has_live_stock=False,
                variants__is_active=True,
                variants__is_preorder=True,
            )
        elif availability == "out_of_stock":
            queryset = queryset.filter(
                has_live_stock=False,
                variants__is_active=True,
                variants__is_preorder=False,
            ).exclude(
                variants__is_active=True,
                variants__is_preorder=True,
            )
        return queryset.distinct()


class PublicProductCategoryListView(generics.ListAPIView):
    serializer_class = PublicProductCategorySerializer
    permission_classes = [AllowAny]
    pagination_class = None

    def get_queryset(self):
        return (
            ProductCategory.objects.filter(
                is_active=True,
                products__is_active=True,
                products__is_published=True,
                products__variants__is_active=True,
            )
            .order_by("display_order", "name")
            .distinct()
        )


class PublicProductDetailView(generics.RetrieveAPIView):
    serializer_class = PublicProductDetailSerializer
    permission_classes = [AllowAny]
    lookup_field = "slug"

    def get_queryset(self):
        return (
            Product.objects.select_related("category")
            .filter(
                is_active=True,
                is_published=True,
                category__is_active=True,
                variants__is_active=True,
            )
            .prefetch_related(Prefetch("variants", queryset=public_variants()))
            .distinct()
        )


class WishlistView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        products = (
            Product.objects.select_related("category")
            .filter(
                wishlist_items__customer=request.user,
                is_active=True,
                is_published=True,
                category__is_active=True,
                variants__is_active=True,
            )
            .prefetch_related(Prefetch("variants", queryset=public_variants()))
            .order_by("-wishlist_items__created_at")
            .distinct()
        )
        return Response(PublicProductSerializer(products, many=True).data)

    def post(self, request):
        slug = str(request.data.get("product_slug", "")).strip()
        if not slug:
            raise ValidationError({"product_slug": "Select a product to save."})
        try:
            product = (
                Product.objects.select_related("category")
                .filter(
                    is_active=True,
                    is_published=True,
                    category__is_active=True,
                    variants__is_active=True,
                )
                .prefetch_related(Prefetch("variants", queryset=public_variants()))
                .distinct()
                .get(slug=slug)
            )
        except Product.DoesNotExist as exc:
            raise ValidationError(
                {"product_slug": "This product is not available."}
            ) from exc
        _, created = WishlistItem.objects.get_or_create(
            customer=request.user,
            product=product,
        )
        return Response(
            PublicProductSerializer(product).data,
            status=status.HTTP_201_CREATED if created else status.HTTP_200_OK,
        )


class WishlistItemDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, product_slug):
        deleted, _ = WishlistItem.objects.filter(
            customer=request.user,
            product__slug=product_slug,
        ).delete()
        if not deleted:
            return Response(
                {"detail": "The product was not in your wishlist."},
                status=status.HTTP_404_NOT_FOUND,
            )
        return Response(status=status.HTTP_204_NO_CONTENT)


class CustomerCartView(APIView):
    permission_classes = [IsAuthenticated]

    def _cart_items(self, user):
        return CustomerCartItem.objects.select_related(
            "variant",
            "variant__product",
            "variant__product__category",
        ).filter(
            customer=user,
            variant__is_active=True,
            variant__product__is_active=True,
            variant__product__is_published=True,
            variant__product__category__is_active=True,
        )

    def get(self, request):
        return Response(
            CustomerCartItemSerializer(
                self._cart_items(request.user), many=True
            ).data
        )

class CartValidationView(APIView):
    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def post(self, request):
        serializer = CartValidationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        items, adjustments = validate_cart_lines(serializer.validated_data["items"])
        if request.user.is_authenticated:
            replace_customer_cart(request.user, items)
        return Response({"items": items, "adjustments": adjustments})


class CustomerCartItemView(APIView):
    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def post(self, request):
        serializer = CartLineSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        line = serializer.validated_data
        quantities = {
            item.variant_id: item.quantity
            for item in CustomerCartItem.objects.select_for_update().filter(
                customer=request.user
            )
        }
        variant_id = line["variant_id"]
        quantities[variant_id] = min(
            20, quantities.get(variant_id, 0) + line["quantity"]
        )
        items, adjustments = validate_cart_lines(
            [
                {"variant_id": item_variant_id, "quantity": quantity}
                for item_variant_id, quantity in quantities.items()
            ]
        )
        replace_customer_cart(request.user, items)
        return Response({"items": items, "adjustments": adjustments})


class CustomerCartItemDetailView(APIView):
    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def patch(self, request, variant_id):
        serializer = CartQuantitySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        cart_items = list(
            CustomerCartItem.objects.select_for_update().filter(
                customer=request.user
            )
        )
        if not any(item.variant_id == variant_id for item in cart_items):
            return Response(
                {"detail": "The product variant is not in your cart."},
                status=status.HTTP_404_NOT_FOUND,
            )
        items, adjustments = validate_cart_lines(
            [
                {
                    "variant_id": item.variant_id,
                    "quantity": (
                        serializer.validated_data["quantity"]
                        if item.variant_id == variant_id
                        else item.quantity
                    ),
                }
                for item in cart_items
            ]
        )
        replace_customer_cart(request.user, items)
        return Response({"items": items, "adjustments": adjustments})

    @transaction.atomic
    def delete(self, request, variant_id):
        cart_items = list(
            CustomerCartItem.objects.select_for_update().filter(
                customer=request.user
            )
        )
        if not any(item.variant_id == variant_id for item in cart_items):
            return Response(
                {"detail": "The product variant is not in your cart."},
                status=status.HTTP_404_NOT_FOUND,
            )
        items, adjustments = validate_cart_lines(
            [
                {"variant_id": item.variant_id, "quantity": item.quantity}
                for item in cart_items
                if item.variant_id != variant_id
            ]
        )
        replace_customer_cart(request.user, items)
        return Response({"items": items, "adjustments": adjustments})


class ManagementProductListView(generics.ListCreateAPIView):
    permission_classes = [IsOwner]
    pagination_class = None

    def get_serializer_class(self):
        if self.request.method == "POST":
            return ManagementProductCreateSerializer
        return ManagementProductListSerializer

    def get_queryset(self):
        inventories = BranchInventory.objects.select_related("branch").order_by(
            "branch__name"
        )
        variants = ProductVariant.objects.prefetch_related(
            Prefetch("branch_inventory", queryset=inventories)
        ).order_by("name")
        return (
            Product.objects.select_related("category")
            .prefetch_related(Prefetch("variants", queryset=variants))
            .order_by("category__display_order", "name")
        )

    def perform_create(self, serializer):
        product = serializer.save()
        record_event(
            action="product.created",
            record_type="Product",
            record_id=product.id,
            actor=self.request.user,
            actor_role=actor_role_for(self.request.user),
            new_values={
                "name": product.name,
                "slug": product.slug,
                "category_id": str(product.category_id),
                "is_active": product.is_active,
                "is_published": product.is_published,
                "variant_ids": [
                    str(variant_id)
                    for variant_id in product.variants.values_list("id", flat=True)
                ],
            },
            ip_address=client_ip(self.request),
            device_identifier=client_device(self.request),
        )


class ManagementProductCategoryOptionListView(generics.ListAPIView):
    serializer_class = ManagementProductCategoryOptionSerializer
    permission_classes = [IsOwner]
    pagination_class = None
    queryset = ProductCategory.objects.filter(is_active=True).order_by(
        "display_order", "name"
    )


class ManagementProductBranchOptionListView(generics.ListAPIView):
    serializer_class = ManagementProductBranchOptionSerializer
    permission_classes = [IsOwner]
    pagination_class = None
    queryset = Branch.objects.filter(is_active=True).order_by("name")


class ManagementProductDetailView(generics.RetrieveUpdateAPIView):
    permission_classes = [IsOwner]
    http_method_names = ["get", "patch", "head", "options"]

    def get_serializer_class(self):
        if self.request.method == "PATCH":
            return ManagementProductUpdateSerializer
        return ManagementProductDetailSerializer

    def get_queryset(self):
        inventories = BranchInventory.objects.select_related("branch").order_by(
            "branch__name"
        )
        variants = ProductVariant.objects.prefetch_related(
            Prefetch("branch_inventory", queryset=inventories)
        ).order_by("name")
        return Product.objects.select_related("category").prefetch_related(
            Prefetch("variants", queryset=variants)
        )

    def perform_update(self, serializer):
        product = self.get_object()
        previous_image = product.image.name if product.image else ""
        previous_values = {
            "name": product.name,
            "category_id": str(product.category_id),
            "is_active": product.is_active,
            "is_published": product.is_published,
            "variant_ids": [
                str(item) for item in product.variants.values_list("id", flat=True)
            ],
        }
        updated = serializer.save()
        if previous_image and updated.image.name != previous_image:
            updated.image.storage.delete(previous_image)
        record_event(
            action="product.updated",
            record_type="Product",
            record_id=updated.id,
            actor=self.request.user,
            actor_role=actor_role_for(self.request.user),
            previous_values=previous_values,
            new_values={
                "name": updated.name,
                "category_id": str(updated.category_id),
                "is_active": updated.is_active,
                "is_published": updated.is_published,
                "variant_ids": [
                    str(item)
                    for item in updated.variants.values_list("id", flat=True)
                ],
            },
            ip_address=client_ip(self.request),
            device_identifier=client_device(self.request),
        )


class ManagementProductCategoryListCreateView(generics.ListCreateAPIView):
    serializer_class = ManagementProductCategorySerializer
    permission_classes = [IsOwner]
    pagination_class = None

    def get_queryset(self):
        return ProductCategory.objects.annotate(
            product_count=Count("products")
        ).order_by("display_order", "name")

    def perform_create(self, serializer):
        category = serializer.save()
        record_event(
            action="product_category.created",
            record_type="ProductCategory",
            record_id=category.id,
            actor=self.request.user,
            actor_role=actor_role_for(self.request.user),
            new_values={
                "name": category.name,
                "slug": category.slug,
                "display_order": category.display_order,
                "is_active": category.is_active,
            },
            ip_address=client_ip(self.request),
            device_identifier=client_device(self.request),
        )


class ManagementProductCategoryDetailView(
    generics.RetrieveUpdateDestroyAPIView
):
    serializer_class = ManagementProductCategorySerializer
    permission_classes = [IsOwner]
    http_method_names = ["get", "patch", "delete", "head", "options"]

    def get_queryset(self):
        return ProductCategory.objects.annotate(product_count=Count("products"))

    def perform_update(self, serializer):
        category = self.get_object()
        previous_values = {
            "name": category.name,
            "description": category.description,
            "display_order": category.display_order,
            "is_active": category.is_active,
        }
        updated = serializer.save()
        record_event(
            action="product_category.updated",
            record_type="ProductCategory",
            record_id=updated.id,
            actor=self.request.user,
            actor_role=actor_role_for(self.request.user),
            previous_values=previous_values,
            new_values={
                "name": updated.name,
                "description": updated.description,
                "display_order": updated.display_order,
                "is_active": updated.is_active,
            },
            ip_address=client_ip(self.request),
            device_identifier=client_device(self.request),
        )

    def perform_destroy(self, instance):
        if instance.products.exists():
            raise serializers.ValidationError(
                {
                    "category": (
                        "Move or remove this category's products before deleting it."
                    )
                }
            )
        record_event(
            action="product_category.deleted",
            record_type="ProductCategory",
            record_id=instance.id,
            actor=self.request.user,
            actor_role=actor_role_for(self.request.user),
            previous_values={"name": instance.name, "slug": instance.slug},
            ip_address=client_ip(self.request),
            device_identifier=client_device(self.request),
        )
        instance.delete()
