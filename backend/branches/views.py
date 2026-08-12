from collections import defaultdict
from decimal import Decimal

from django.db.models import F, Q, Sum
from django.utils import timezone
from rest_framework import generics, serializers, status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.models import User
from bookings.models import Booking
from inventory.models import BranchInventory
from orders.models import Order
from payments.models import Invoice, Payment
from products.models import ProductCategory, ProductVariant
from services.models import ServiceCategory

from .models import Branch, BranchStaffAssignment
from .permissions import (
    MANAGEMENT_PORTAL_ROLES,
    IsOwner,
    IsOwnerOrAssignedBranchStaff,
    get_accessible_branch_ids,
    is_owner,
)
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


class ManagementOverviewView(APIView):
    """Describe the signed-in staff member's management operating scope."""

    permission_classes = [IsOwnerOrAssignedBranchStaff]
    required_branch_roles = (
        BranchStaffAssignment.Role.MANAGER,
        BranchStaffAssignment.Role.RECEPTIONIST,
        BranchStaffAssignment.Role.SERVICE_PROVIDER,
    )

    class FilterSerializer(serializers.Serializer):
        date_from = serializers.DateField(required=False)
        date_to = serializers.DateField(required=False)
        branch = serializers.UUIDField(required=False)
        product_category = serializers.UUIDField(required=False)
        service_category = serializers.UUIDField(required=False)
        payment_method = serializers.CharField(required=False, max_length=40)
        booking_status = serializers.ChoiceField(
            choices=Booking.Status.choices,
            required=False,
        )
        order_status = serializers.ChoiceField(
            choices=Order.Status.choices,
            required=False,
        )

        def validate(self, attrs):
            if (
                attrs.get("date_from")
                and attrs.get("date_to")
                and attrs["date_from"] > attrs["date_to"]
            ):
                raise serializers.ValidationError(
                    {"date_to": "The end date cannot be before the start date."}
                )
            return attrs

    def get(self, request):
        owner_access = is_owner(request.user)
        branch_ids = get_accessible_branch_ids(
            request.user,
            self.required_branch_roles,
        )
        filter_serializer = self.FilterSerializer(data=request.query_params)
        filter_serializer.is_valid(raise_exception=True)
        filters = filter_serializer.validated_data
        accessible_branch_ids = set(branch_ids)
        selected_branch = filters.get("branch")
        if selected_branch:
            if selected_branch not in branch_ids:
                raise serializers.ValidationError(
                    {"branch": "This branch is outside your authorized scope."}
                )
            branch_ids = {selected_branch}

        accessible_branches = Branch.objects.filter(pk__in=accessible_branch_ids)
        if not owner_access:
            accessible_branches = accessible_branches.filter(is_active=True)
        accessible_branches = list(accessible_branches.order_by("name"))
        branches = [
            branch for branch in accessible_branches if branch.pk in branch_ids
        ]

        roles_by_branch = defaultdict(list)
        if not owner_access:
            assignments = BranchStaffAssignment.objects.filter(
                staff=request.user,
                branch__in=branches,
                is_active=True,
            ).values_list("branch_id", "roles")
            for branch_id, roles in assignments:
                roles_by_branch[branch_id] = [
                    role
                    for role in roles or []
                    if role in MANAGEMENT_PORTAL_ROLES
                ]

        bookings = Booking.objects.filter(branch_id__in=branch_ids)
        orders = Order.objects.filter(branch_id__in=branch_ids)
        payments = Payment.objects.filter(branch_id__in=branch_ids)
        invoices = Invoice.objects.filter(branch_id__in=branch_ids)
        inventory = BranchInventory.objects.filter(branch_id__in=branch_ids)
        payment_method_options = list(
            Payment.objects.filter(branch_id__in=accessible_branch_ids)
            .exclude(method="")
            .values_list("method", flat=True)
            .distinct()
            .order_by("method")
        )

        date_from = filters.get("date_from")
        date_to = filters.get("date_to")
        if date_from:
            bookings = bookings.filter(preferred_start__date__gte=date_from)
            orders = orders.filter(created_at__date__gte=date_from)
            payments = payments.filter(paid_at__date__gte=date_from)
            invoices = invoices.filter(issued_at__date__gte=date_from)
        if date_to:
            bookings = bookings.filter(preferred_start__date__lte=date_to)
            orders = orders.filter(created_at__date__lte=date_to)
            payments = payments.filter(paid_at__date__lte=date_to)
            invoices = invoices.filter(issued_at__date__lte=date_to)

        product_category = filters.get("product_category")
        if product_category:
            matching_order_ids = orders.filter(
                items__product_variant__product__category_id=product_category,
            ).values("pk")
            orders = orders.filter(pk__in=matching_order_ids)
            payments = payments.filter(order_id__in=matching_order_ids)
            invoices = invoices.filter(order_id__in=matching_order_ids)
            inventory = inventory.filter(
                product_variant__product__category_id=product_category
            )

        service_category = filters.get("service_category")
        if service_category:
            matching_booking_ids = bookings.filter(
                service_items__service__category_id=service_category,
            ).values("pk")
            bookings = bookings.filter(pk__in=matching_booking_ids)
            payments = payments.filter(booking_id__in=matching_booking_ids)
            invoices = invoices.filter(booking_id__in=matching_booking_ids)

        booking_status = filters.get("booking_status")
        if booking_status:
            bookings = bookings.filter(status=booking_status)
            payments = payments.filter(
                Q(booking__isnull=True) | Q(booking__status=booking_status)
            )
            invoices = invoices.filter(
                Q(booking__isnull=True) | Q(booking__status=booking_status)
            )

        order_status = filters.get("order_status")
        if order_status:
            orders = orders.filter(status=order_status)
            payments = payments.filter(
                Q(order__isnull=True) | Q(order__status=order_status)
            )
            invoices = invoices.filter(
                Q(order__isnull=True) | Q(order__status=order_status)
            )

        payment_method = filters.get("payment_method")
        if payment_method:
            payments = payments.filter(method=payment_method)

        appointment_queryset = bookings
        if not date_from and not date_to:
            appointment_queryset = appointment_queryset.filter(
                preferred_start__date=timezone.localdate()
            )
        today_appointments = appointment_queryset.exclude(
            status__in=(Booking.Status.CANCELLED, Booking.Status.REJECTED)
        ).count()
        pending_booking_requests = bookings.filter(
            status=Booking.Status.PENDING,
        ).count()
        proposed_changes_awaiting_acceptance = bookings.filter(
            Q(proposed_expires_at__isnull=True)
            | Q(proposed_expires_at__gt=timezone.now()),
            status=Booking.Status.PROPOSED,
            proposed_start__isnull=False,
        ).count()
        today_payment_queryset = payments
        if not date_from and not date_to:
            today_payment_queryset = today_payment_queryset.filter(
                paid_at__date=timezone.localdate()
            )
        today_sales = (
            today_payment_queryset.filter(
                status=Payment.Status.SUCCEEDED,
                currency="GHS",
            ).aggregate(total=Sum("amount"))["total"]
            or Decimal("0.00")
        )
        product_revenue = (
            payments.filter(
                status=Payment.Status.SUCCEEDED,
                order__isnull=False,
                currency="GHS",
            ).aggregate(total=Sum("amount"))["total"]
            or Decimal("0.00")
        )
        service_revenue = (
            payments.filter(
                status=Payment.Status.SUCCEEDED,
                booking__isnull=False,
                currency="GHS",
            ).aggregate(total=Sum("amount"))["total"]
            or Decimal("0.00")
        )
        outstanding_balances = (
            invoices.filter(
                status=Invoice.Status.OPEN,
                currency="GHS",
            ).aggregate(total=Sum("total_amount"))["total"]
            or Decimal("0.00")
        )
        pending_online_orders = orders.filter(
            status__in=(
                Order.Status.AWAITING_PAYMENT,
                Order.Status.PAYMENT_UNDER_REVIEW,
                Order.Status.PAID,
                Order.Status.PROCESSING,
                Order.Status.READY_FOR_PICKUP,
                Order.Status.SHIPPED,
            ),
        ).count()
        low_stock_products = inventory.filter(
            quantity_on_hand__lte=(
                F("quantity_reserved") + F("reorder_level")
            ),
        ).count()
        branch_comparison = []
        for branch in branches:
            branch_payments = today_payment_queryset.filter(branch=branch)
            branch_comparison.append(
                {
                    "id": str(branch.pk),
                    "code": branch.code,
                    "name": branch.name,
                    "appointments": appointment_queryset.filter(branch=branch)
                    .exclude(status__in=(Booking.Status.CANCELLED, Booking.Status.REJECTED))
                    .count(),
                    "sales": f"{(branch_payments.filter(status=Payment.Status.SUCCEEDED, currency='GHS').aggregate(total=Sum('amount'))['total'] or Decimal('0.00')):.2f}",
                    "pending_orders": orders.filter(
                        branch=branch,
                        status__in=(Order.Status.AWAITING_PAYMENT, Order.Status.PAYMENT_UNDER_REVIEW, Order.Status.PAID, Order.Status.PROCESSING, Order.Status.READY_FOR_PICKUP, Order.Status.SHIPPED),
                    ).count(),
                    "low_stock": inventory.filter(
                        branch=branch,
                        quantity_on_hand__lte=F("quantity_reserved") + F("reorder_level"),
                    ).count(),
                }
            )

        return Response(
            {
                "staff": {
                    "id": str(request.user.pk),
                    "full_name": request.user.full_name,
                    "is_owner": owner_access,
                    "scope_label": (
                        "All branches"
                        if owner_access
                        else f"{len(branches)} assigned branch"
                        + ("" if len(branches) == 1 else "es")
                    ),
                },
                "branches": [
                    {
                        "id": str(branch.pk),
                        "code": branch.code,
                        "name": branch.name,
                        "is_active": branch.is_active,
                        "roles": (
                            ["owner"]
                            if owner_access
                            else roles_by_branch[branch.pk]
                        ),
                    }
                    for branch in branches
                ],
                "filter_options": {
                    "branches": [
                        {
                            "id": str(branch.pk),
                            "code": branch.code,
                            "name": branch.name,
                        }
                        for branch in accessible_branches
                    ],
                    "product_categories": [
                        {"id": str(category.pk), "name": category.name}
                        for category in ProductCategory.objects.filter(
                            is_active=True
                        ).order_by("display_order", "name")
                    ],
                    "service_categories": [
                        {"id": str(category.pk), "name": category.name}
                        for category in ServiceCategory.objects.filter(
                            is_active=True
                        ).order_by("display_order", "name")
                    ],
                    "payment_methods": [
                        {
                            "value": method,
                            "label": method.replace("_", " ").title(),
                        }
                        for method in payment_method_options
                    ],
                    "booking_statuses": [
                        {"value": value, "label": label}
                        for value, label in Booking.Status.choices
                    ],
                    "order_statuses": [
                        {"value": value, "label": label}
                        for value, label in Order.Status.choices
                    ],
                },
                "branch_comparison": branch_comparison,
                "summary": {
                    "today_appointments": today_appointments,
                    "pending_booking_requests": pending_booking_requests,
                    "proposed_changes_awaiting_acceptance": (
                        proposed_changes_awaiting_acceptance
                    ),
                    "today_sales": f"{today_sales:.2f}",
                    "product_revenue": f"{product_revenue:.2f}",
                    "service_revenue": f"{service_revenue:.2f}",
                    "outstanding_balances": f"{outstanding_balances:.2f}",
                    "pending_online_orders": pending_online_orders,
                    "low_stock_products": low_stock_products,
                },
            }
        )


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
