from decimal import Decimal

from django.db.models import Sum
from django.utils import timezone
from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from bookings.models import Booking, BookingServiceItem
from orders.models import Order
from payments.models import Invoice
from auditlog.services import actor_role_for, client_device, client_ip, record_event
from .models import CustomerAddress, CustomerConsent
from .serializers import CustomerAddressSerializer, CustomerConsentSerializer


UPCOMING_STATUSES = (
    Booking.Status.PENDING,
    Booking.Status.PROPOSED,
    Booking.Status.CONFIRMED,
    Booking.Status.RESCHEDULED,
)


def money(value):
    return f"{Decimal(value or 0):.2f}"


class CustomerAddressListCreateView(generics.ListCreateAPIView):
    serializer_class = CustomerAddressSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return CustomerAddress.objects.filter(customer=self.request.user)


class CustomerAddressDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = CustomerAddressSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return CustomerAddress.objects.filter(customer=self.request.user)


class CustomerConsentView(generics.RetrieveUpdateAPIView):
    serializer_class = CustomerConsentSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        now = timezone.now()
        consent, _ = CustomerConsent.objects.get_or_create(
            user=self.request.user,
            defaults={
                "terms_version": "draft-2026-07",
                "privacy_version": "draft-2026-07",
                "terms_privacy_accepted_at": now,
                "marketing_consent": False,
                "marketing_consent_updated_at": now,
                "photograph_consent": False,
            },
        )
        return consent

    def perform_update(self, serializer):
        consent = self.get_object()
        previous = {
            "marketing_consent": consent.marketing_consent,
            "photograph_consent": consent.photograph_consent,
        }
        updated = serializer.save()
        record_event(
            action="customer.consent_updated",
            record_type="customer_consent",
            record_id=updated.pk,
            actor=self.request.user,
            actor_role=actor_role_for(self.request.user),
            previous_values=previous,
            new_values={
                "marketing_consent": updated.marketing_consent,
                "photograph_consent": updated.photograph_consent,
            },
            ip_address=client_ip(self.request),
            device_identifier=client_device(self.request),
        )


class CustomerAccountOverviewView(APIView):
    """Return customer-scoped dashboard totals and compact recent records."""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        bookings = Booking.objects.filter(customer=request.user)
        orders = Order.objects.filter(customer=request.user)
        upcoming_queryset = bookings.filter(
            preferred_start__gte=timezone.now(), status__in=UPCOMING_STATUSES
        )
        upcoming = list(
            upcoming_queryset.select_related("branch")
            .prefetch_related("service_items")
            .order_by("preferred_start")[:3]
        )
        completed_services = BookingServiceItem.objects.filter(
            booking__customer=request.user,
            booking__status=Booking.Status.COMPLETED,
        ).count()
        outstanding = (
            Invoice.objects.filter(
                customer=request.user, status=Invoice.Status.OPEN
            ).aggregate(total=Sum("total_amount"))["total"]
            or Decimal("0.00")
        )
        recent_orders = list(
            orders.select_related("branch").prefetch_related("items")[:3]
        )

        booking_activity = [
            {
                "id": f"booking-{booking.pk}",
                "type": "booking",
                "reference": booking.reference,
                "title": "Booking updated",
                "description": ", ".join(
                    item.service_name for item in booking.service_items.all()
                ) or "Service appointment",
                "status": booking.status,
                "timestamp": booking.updated_at,
                "action_url": f"/account/appointments/{booking.reference}",
            }
            for booking in bookings.prefetch_related("service_items").order_by(
                "-updated_at"
            )[:5]
        ]
        order_activity = [
            {
                "id": f"order-{order.pk}",
                "type": "order",
                "reference": order.reference,
                "title": "Order updated",
                "description": f"{order.items.count()} product line(s)",
                "status": order.status,
                "timestamp": order.updated_at,
                "action_url": f"/checkout/success?order={order.reference}",
            }
            for order in orders.prefetch_related("items").order_by("-updated_at")[:5]
        ]
        activity = sorted(
            booking_activity + order_activity,
            key=lambda item: item["timestamp"],
            reverse=True,
        )[:6]

        return Response(
            {
                "summary": {
                    "upcoming_appointments": upcoming_queryset.count(),
                    "completed_services": completed_services,
                    "orders": orders.count(),
                    "outstanding_balance": money(outstanding),
                    "currency": "GHS",
                },
                "upcoming_appointments": [
                    {
                        "reference": booking.reference,
                        "branch_name": booking.branch.name,
                        "preferred_start": booking.preferred_start,
                        "status": booking.status,
                        "services": [
                            item.service_name for item in booking.service_items.all()
                        ],
                        "total_amount": money(booking.total_amount),
                    }
                    for booking in upcoming
                ],
                "recent_orders": [
                    {
                        "reference": order.reference,
                        "branch_name": order.branch.name,
                        "status": order.status,
                        "payment_status": order.payment_status,
                        "total_amount": money(order.total_amount),
                        "item_count": sum(item.quantity for item in order.items.all()),
                        "created_at": order.created_at,
                    }
                    for order in recent_orders
                ],
                "recent_activity": activity,
            }
        )
