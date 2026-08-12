from collections import defaultdict
from datetime import timedelta
from decimal import Decimal
from uuid import UUID

from django.db import transaction
from django.db.models import Sum
from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework import generics, status
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from branches.models import Branch
from inventory.models import BranchInventory, StockMovement
from products.models import CustomerCartItem
from payments.services import issue_invoice_for_source
from notifications.jobs import enqueue_email_job

from .models import Order, OrderItem, StockReservation
from .serializers import CheckoutCreateSerializer, OrderDetailSerializer, OrderSerializer
from .services import release_expired_for_inventories, release_order_reservations


User = get_user_model()


def order_queryset():
    return Order.objects.select_related("branch", "customer", "invoice").prefetch_related(
        "items", "stock_reservations", "payments__receipt"
    )


def cart_items_for(user, *, lock=False):
    queryset = CustomerCartItem.objects.select_related(
        "variant", "variant__product", "variant__product__category"
    ).filter(
        customer=user,
        variant__is_active=True,
        variant__product__is_active=True,
        variant__product__is_published=True,
        variant__product__category__is_active=True,
    )
    return list(queryset.select_for_update() if lock else queryset)


def cart_quantities(items):
    return {item.variant_id: item.quantity for item in items}


def eligible_branch_rows(items):
    requested = cart_quantities(items)
    if not requested:
        return []
    now = timezone.now()
    expired_by_inventory = {
        row["inventory_id"]: row["quantity"] or 0
        for row in StockReservation.objects.filter(
            inventory__product_variant_id__in=requested,
            status=StockReservation.Status.ACTIVE,
            expires_at__lte=now,
        )
        .values("inventory_id")
        .annotate(quantity=Sum("quantity"))
    }
    branches = list(Branch.objects.filter(is_active=True).order_by("name"))
    rows = {
        (row.branch_id, row.product_variant_id): row
        for row in BranchInventory.objects.filter(
            branch__in=branches,
            product_variant_id__in=requested,
            is_available=True,
        )
    }
    eligible = []
    for branch in branches:
        if all(
            (row := rows.get((branch.id, variant_id)))
            and (
                row.quantity_on_hand
                - row.quantity_reserved
                + expired_by_inventory.get(row.id, 0)
            )
            >= quantity
            for variant_id, quantity in requested.items()
        ):
            eligible.append(branch)
    return eligible


class CheckoutOptionsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        items = cart_items_for(request.user)
        branches = eligible_branch_rows(items)
        subtotal = sum(
            (item.variant.selling_price * item.quantity for item in items),
            Decimal("0.00"),
        )
        return Response(
            {
                "customer": {
                    "name": request.user.full_name,
                    "phone": request.user.phone_number,
                    "email": request.user.email,
                },
                "items": [
                    {
                        "variant_id": str(item.variant_id),
                        "product_name": item.variant.product.name,
                        "variant_name": item.variant.name,
                        "sku": item.variant.sku,
                        "image_path": (
                            item.variant.product.image.url
                            if item.variant.product.image
                            else item.variant.product.image_path
                        ),
                        "unit_price": item.variant.selling_price,
                        "quantity": item.quantity,
                        "line_total": item.variant.selling_price * item.quantity,
                    }
                    for item in items
                ],
                "subtotal": subtotal,
                "delivery_fee": Decimal("0.00"),
                "total_amount": subtotal,
                "pickup_branches": [
                    {"id": str(branch.id), "code": branch.code, "name": branch.name}
                    for branch in branches
                ],
                "delivery_available": bool(branches),
                "reservation_minutes": 30,
            }
        )


class CheckoutCreateView(APIView):
    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def post(self, request):
        try:
            request_id = UUID(str(request.data.get("client_request_id")))
        except (TypeError, ValueError):
            request_id = None
        User.objects.select_for_update().get(pk=request.user.pk)
        existing = (
            order_queryset()
            .filter(customer=request.user, client_request_id=request_id)
            .first()
            if request_id
            else None
        )
        if existing:
            return Response(OrderSerializer(existing).data)

        serializer = CheckoutCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        items = cart_items_for(request.user, lock=True)
        if not items:
            return Response(
                {"detail": "Your cart is empty or its products are unavailable."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        requested_branch = serializer.validated_data.pop("_requested_branch")
        eligible = eligible_branch_rows(items)
        if requested_branch:
            if requested_branch not in eligible:
                return Response(
                    {"detail": "This branch can no longer fulfil every cart item."},
                    status=status.HTTP_409_CONFLICT,
                )
            branch = requested_branch
        else:
            branch = eligible[0] if eligible else None
            if not branch:
                return Response(
                    {"detail": "Delivery cannot currently be fulfilled from available stock."},
                    status=status.HTTP_409_CONFLICT,
                )

        variant_ids = [item.variant_id for item in items]
        inventories = list(
            BranchInventory.objects.select_for_update()
            .filter(
                branch=branch,
                product_variant_id__in=variant_ids,
                is_available=True,
            )
            .order_by("product_variant_id")
        )
        release_expired_for_inventories(inventories)
        inventory_by_variant = {
            inventory.product_variant_id: inventory for inventory in inventories
        }
        for item in items:
            inventory = inventory_by_variant.get(item.variant_id)
            if not inventory or inventory.quantity_available < item.quantity:
                return Response(
                    {
                        "detail": (
                            f"{item.variant.product.name} no longer has sufficient "
                            f"stock at {branch.name}."
                        )
                    },
                    status=status.HTTP_409_CONFLICT,
                )

        expires_at = timezone.now() + timedelta(minutes=30)
        subtotal = sum(
            (item.variant.selling_price * item.quantity for item in items),
            Decimal("0.00"),
        )
        validated = serializer.validated_data
        order = Order.objects.create(
            customer=request.user,
            branch=branch,
            client_request_id=validated["client_request_id"],
            fulfillment_method=validated["fulfillment_method"],
            recipient_name=validated["recipient_name"],
            recipient_phone=validated["recipient_phone"],
            delivery_address=validated.get("delivery_address", ""),
            delivery_city=validated.get("delivery_city", ""),
            delivery_notes=validated.get("delivery_notes", ""),
            subtotal=subtotal,
            total_amount=subtotal,
            reservation_expires_at=expires_at,
            created_by=request.user,
            updated_by=request.user,
        )
        for cart_item in items:
            variant = cart_item.variant
            product = variant.product
            line_total = variant.selling_price * cart_item.quantity
            order_item = OrderItem.objects.create(
                order=order,
                product_variant=variant,
                product_name=product.name,
                product_slug=product.slug,
                variant_name=variant.name,
                sku=variant.sku,
                image_path=product.image.url if product.image else product.image_path,
                unit_price=variant.selling_price,
                quantity=cart_item.quantity,
                line_total=line_total,
            )
            inventory = inventory_by_variant[variant.id]
            inventory.quantity_reserved += cart_item.quantity
            inventory.save(update_fields=["quantity_reserved", "updated_at"])
            StockReservation.objects.create(
                order=order,
                order_item=order_item,
                inventory=inventory,
                quantity=cart_item.quantity,
                expires_at=expires_at,
            )
            StockMovement.objects.create(
                inventory=inventory,
                movement_type=StockMovement.MovementType.RESERVATION,
                quantity_reserved_change=cart_item.quantity,
                quantity_on_hand_after=inventory.quantity_on_hand,
                quantity_reserved_after=inventory.quantity_reserved,
                reference_type="order",
                reference_id=order.reference,
                note="Stock reserved for checkout for 30 minutes.",
                performed_by=request.user,
            )
        CustomerCartItem.objects.filter(customer=request.user).delete()
        issue_invoice_for_source(order)
        transaction.on_commit(
            lambda order_id=order.pk: enqueue_email_job(
                job_type="order_confirmation",
                object_id=order_id,
                unique_key=f"order:{order_id}:confirmation",
            )
        )
        return Response(
            OrderSerializer(order_queryset().get(pk=order.pk)).data,
            status=status.HTTP_201_CREATED,
        )


class CustomerOrderListView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = OrderSerializer

    def get_queryset(self):
        queryset = order_queryset().filter(customer=self.request.user)
        requested_status = self.request.query_params.get("status", "").strip()
        if requested_status:
            if requested_status not in Order.Status.values:
                raise ValidationError({"status": ["Select a valid order status."]})
            queryset = queryset.filter(status=requested_status)
        return queryset


class CustomerOrderDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, reference):
        order = order_queryset().filter(
            customer=request.user, reference=reference
        ).first()
        if not order:
            return Response({"detail": "Order was not found."}, status=404)
        return Response(OrderDetailSerializer(order).data)


class CustomerOrderCancelView(APIView):
    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def post(self, request, reference):
        order = Order.objects.filter(
            customer=request.user,
            reference=reference,
            status__in=(
                Order.Status.AWAITING_PAYMENT,
                Order.Status.PAYMENT_UNDER_REVIEW,
            ),
        ).first()
        if not order:
            return Response(
                {"detail": "This order cannot be cancelled or was not found."},
                status=400,
            )
        release_order_reservations(
            order, actor=request.user, reason="Customer cancelled checkout."
        )
        order.status = Order.Status.CANCELLED
        order.payment_status = "cancelled"
        order.cancelled_at = timezone.now()
        order.updated_by = request.user
        order.save(
            update_fields=[
                "status", "payment_status", "cancelled_at", "updated_by",
                "updated_at",
            ]
        )
        transaction.on_commit(
            lambda order_id=order.pk, updated=str(order.updated_at): enqueue_email_job(
                job_type="order_status",
                object_id=order_id,
                event=Order.Status.CANCELLED,
                unique_key=f"order:{order_id}:cancelled:{updated}",
            )
        )
        for item in order.items.select_related("product_variant"):
            variant = item.product_variant
            if variant.is_active and variant.product.is_active and variant.product.is_published:
                CustomerCartItem.objects.update_or_create(
                    customer=request.user,
                    variant=variant,
                    defaults={"quantity": min(item.quantity, 20)},
                )
        return Response(OrderSerializer(order_queryset().get(pk=order.pk)).data)
