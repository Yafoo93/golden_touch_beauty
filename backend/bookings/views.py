from datetime import datetime, time, timedelta
from uuid import UUID

from django.db import transaction
from django.utils import timezone
from rest_framework import generics, status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.exceptions import PermissionDenied
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView

from branches.models import Branch, BranchStaffAssignment
from accounts.models import User
from services.models import Service
from branches.permissions import (
    BranchAccessQuerysetMixin,
    IsOwnerOrAssignedBranchStaff,
    can_access_branch,
)
from notifications.jobs import enqueue_email_job
from payments.services import issue_invoice_for_source
from core.throttling import UnsafeMethodScopedRateThrottle

from .models import Booking, BookingBlock, BookingHistory
from .reminders import schedule_booking_reminders
from .serializers import (
    BookingActionSerializer,
    BookingBlockSerializer,
    BookingCreateSerializer,
    BookingSerializer,
    CustomerBookingSerializer,
)


def booking_queryset():
    return Booking.objects.select_related("branch", "customer").prefetch_related(
        "service_items", "history", "history__actor"
    )


class CustomerBookingListCreateView(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated]
    throttle_classes = [UnsafeMethodScopedRateThrottle]
    throttle_scope = "payment-customer"

    def get_serializer_class(self):
        return (
            BookingCreateSerializer
            if self.request.method == "POST"
            else CustomerBookingSerializer
        )

    def get_queryset(self):
        queryset = booking_queryset().filter(customer=self.request.user)
        requested_status = self.request.query_params.get("status", "").strip()
        if requested_status:
            if requested_status not in Booking.Status.values:
                raise ValidationError({"status": "Select a valid booking status."})
            queryset = queryset.filter(status=requested_status)
        return queryset

    def create(self, request, *args, **kwargs):
        request_id = request.data.get("client_request_id")
        try:
            parsed_request_id = UUID(str(request_id))
        except (TypeError, ValueError):
            parsed_request_id = None
        existing = (
            Booking.objects.filter(
                customer=request.user, client_request_id=parsed_request_id
            ).first()
            if parsed_request_id
            else None
        )
        if existing:
            return Response(CustomerBookingSerializer(existing).data)
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        booking = serializer.save()
        enqueue_email_job(
            job_type="booking_confirmation",
            object_id=booking.pk,
            unique_key=f"booking:{booking.pk}:confirmation",
        )
        return Response(
            CustomerBookingSerializer(booking_queryset().get(pk=booking.pk)).data,
            status=status.HTTP_201_CREATED,
        )


class CustomerBookingDetailView(generics.RetrieveAPIView):
    serializer_class = CustomerBookingSerializer
    permission_classes = [IsAuthenticated]
    lookup_field = "reference"

    def get_queryset(self):
        return booking_queryset().filter(customer=self.request.user)


class CustomerBookingProposalView(APIView):
    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def post(self, request, reference):
        booking = (
            Booking.objects.select_for_update()
            .filter(reference=reference, customer=request.user)
            .first()
        )
        if not booking:
            return Response({"detail": "Booking was not found."}, status=404)
        if booking.status != Booking.Status.PROPOSED or not booking.proposed_start:
            return Response({"detail": "This booking has no proposed time awaiting acceptance."}, status=400)
        if booking.proposed_expires_at and booking.proposed_expires_at < timezone.now():
            return Response({"detail": "The proposed time has expired."}, status=400)
        accepted = bool(request.data.get("accepted"))
        previous = booking.status
        if accepted:
            booking.preferred_start = booking.proposed_start
            booking.status = Booking.Status.CONFIRMED
            action = "proposed_time_accepted"
        else:
            booking.status = Booking.Status.PENDING
            action = "proposed_time_declined"
        booking.proposed_start = None
        booking.proposed_expires_at = None
        booking.updated_by = request.user
        booking.save()
        BookingHistory.objects.create(
            booking=booking,
            action=action,
            from_status=previous,
            to_status=booking.status,
            actor=request.user,
        )
        if accepted:
            transaction.on_commit(
                lambda booking_id=booking.pk, updated=str(booking.updated_at): (
                    enqueue_email_job(
                        job_type="booking_update",
                        object_id=booking_id,
                        event="proposed_time_accepted",
                        unique_key=f"booking:{booking_id}:proposed_time_accepted:{updated}",
                    ),
                    schedule_booking_reminders(Booking.objects.get(pk=booking_id)),
                )
            )
        return Response(
            CustomerBookingSerializer(booking_queryset().get(pk=booking.pk)).data
        )


class BookingAvailabilityView(APIView):
    # Appointment availability is intentionally public so visitors can inspect
    # open times before signing in.  Declare this explicitly: an empty list can
    # otherwise conceal an accidental permission bypass during reviews.
    permission_classes = [AllowAny]

    def get(self, request):
        branch = Branch.objects.filter(
            code__iexact=request.query_params.get("branch", ""), is_active=True
        ).first()
        try:
            selected_date = datetime.strptime(
                request.query_params.get("date", ""), "%Y-%m-%d"
            ).date()
            duration = max(30, min(1440, int(request.query_params.get("duration", "60"))))
        except (TypeError, ValueError):
            return Response({"detail": "Provide a valid branch, date, and duration."}, status=400)
        if not branch:
            return Response({"detail": "Branch was not found."}, status=404)
        day_name = selected_date.strftime("%A").lower()
        if day_name not in [str(day).lower() for day in branch.opening_days]:
            return Response({"slots": [], "closed": True})
        tz = timezone.get_current_timezone()
        opening = timezone.make_aware(datetime.combine(selected_date, branch.opening_time), tz)
        closing = timezone.make_aware(datetime.combine(selected_date, branch.closing_time), tz)
        day_end = timezone.make_aware(datetime.combine(selected_date, time.max), tz)
        blocks = BookingBlock.objects.filter(
            branch=branch,
            is_active=True,
            starts_at__lte=day_end,
            ends_at__gte=opening,
        )
        active = Booking.objects.filter(
            branch=branch,
            status__in=(
                Booking.Status.CONFIRMED,
                Booking.Status.CHECKED_IN,
                Booking.Status.IN_PROGRESS,
            ),
            preferred_start__date=selected_date,
        )
        slots = []
        current = opening
        while current < closing:
            finish = current + timedelta(minutes=duration)
            blocked = blocks.filter(starts_at__lt=finish, ends_at__gt=current).exists()
            occupied = any(
                existing.preferred_start < finish
                and existing.preferred_start
                + timedelta(minutes=existing.total_duration_minutes)
                > current
                for existing in active
            )
            if not blocked and not occupied and current > timezone.now():
                slots.append(
                    {
                        "value": current.isoformat(),
                        "label": current.strftime("%I:%M %p").lstrip("0"),
                        "would_finish_after_closing": finish > closing,
                    }
                )
            current += timedelta(minutes=30)
        return Response({"slots": slots, "closed": False})


class ManagementBookingListCreateView(
    BranchAccessQuerysetMixin, generics.ListCreateAPIView
):
    permission_classes = [IsOwnerOrAssignedBranchStaff]
    required_branch_roles = (BranchStaffAssignment.Role.MANAGER, BranchStaffAssignment.Role.RECEPTIONIST, BranchStaffAssignment.Role.SERVICE_PROVIDER)
    queryset = booking_queryset()

    def get_serializer_class(self):
        return BookingCreateSerializer if self.request.method == "POST" else BookingSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        branch = self.request.query_params.get("branch")
        booking_status = self.request.query_params.get("status")
        if branch:
            queryset = queryset.filter(branch__code__iexact=branch)
        if booking_status:
            queryset = queryset.filter(status=booking_status)
        return queryset

    def create(self, request, *args, **kwargs):
        try:
            request_id = UUID(str(request.data.get("client_request_id")))
        except (TypeError, ValueError):
            request_id = None
        existing = (
            self.get_queryset().filter(client_request_id=request_id).first()
            if request_id
            else None
        )
        if existing:
            return Response(BookingSerializer(existing).data)
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        branch = serializer.validated_data["_branch"]
        if not can_access_branch(request.user, branch, self.required_branch_roles):
            raise PermissionDenied("You are not assigned to this branch.")
        booking = serializer.save()
        enqueue_email_job(
            job_type="booking_confirmation",
            object_id=booking.pk,
            unique_key=f"booking:{booking.pk}:confirmation",
        )
        return Response(
            BookingSerializer(booking_queryset().get(pk=booking.pk)).data,
            status=status.HTTP_201_CREATED,
        )


class ManagementBookingOptionsView(APIView):
    permission_classes = [IsAuthenticated, IsOwnerOrAssignedBranchStaff]
    required_branch_roles = ManagementBookingListCreateView.required_branch_roles

    def get(self, request):
        if request.user.is_superuser:
            branches = Branch.objects.filter(is_active=True)
        else:
            from branches.permissions import get_accessible_branch_ids
            branches = Branch.objects.filter(
                id__in=get_accessible_branch_ids(request.user, self.required_branch_roles), is_active=True
            )
        services = Service.objects.filter(
            branch_availability__branch__in=branches,
            branch_availability__is_available=True,
            is_active=True,
            is_published=True,
        ).distinct()
        customers = User.objects.filter(is_active=True, is_staff=False).order_by("full_name")
        return Response(
            {
                "branches": [
                    {"id": str(branch.id), "code": branch.code, "name": branch.name}
                    for branch in branches
                ],
                "services": [
                    {
                        "id": str(service.id),
                        "name": service.name,
                        "price": service.price,
                        "duration_minutes": service.duration_minutes,
                        "branch_codes": list(
                            service.branch_availability.filter(is_available=True).values_list(
                                "branch__code", flat=True
                            )
                        ),
                    }
                    for service in services
                ],
                "customers": [
                    {
                        "id": str(customer.id),
                        "name": customer.full_name,
                        "email": customer.email,
                        "phone": customer.phone_number,
                    }
                    for customer in customers
                ],
            }
        )


class ManagementBookingDetailView(
    BranchAccessQuerysetMixin, generics.RetrieveAPIView
):
    serializer_class = BookingSerializer
    permission_classes = [IsOwnerOrAssignedBranchStaff]
    required_branch_roles = ManagementBookingListCreateView.required_branch_roles
    queryset = booking_queryset()
    lookup_field = "reference"


class ManagementBookingActionView(APIView):
    permission_classes = [IsOwnerOrAssignedBranchStaff]
    required_branch_roles = ManagementBookingListCreateView.required_branch_roles

    transitions = {
        "confirm": Booking.Status.CONFIRMED,
        "reject": Booking.Status.REJECTED,
        "cancel": Booking.Status.CANCELLED,
        "check_in": Booking.Status.CHECKED_IN,
        "start": Booking.Status.IN_PROGRESS,
        "complete": Booking.Status.COMPLETED,
        "no_show": Booking.Status.NO_SHOW,
        "propose_time": Booking.Status.PROPOSED,
        "confirm_price": Booking.Status.PENDING,
    }
    allowed_from = {
        "confirm": {Booking.Status.PENDING},
        "reject": {Booking.Status.PENDING},
        "cancel": {
            Booking.Status.PENDING,
            Booking.Status.CONFIRMED,
            Booking.Status.PROPOSED,
            Booking.Status.RESCHEDULED,
        },
        "check_in": {Booking.Status.CONFIRMED, Booking.Status.RESCHEDULED},
        "start": {Booking.Status.CHECKED_IN},
        "complete": {Booking.Status.IN_PROGRESS},
        "no_show": {Booking.Status.CONFIRMED, Booking.Status.RESCHEDULED},
        "propose_time": {
            Booking.Status.PENDING,
            Booking.Status.CONFIRMED,
            Booking.Status.RESCHEDULED,
        },
        "confirm_price": {Booking.Status.PENDING, Booking.Status.PROPOSED},
    }

    @transaction.atomic
    def post(self, request, reference):
        booking = Booking.objects.select_for_update().filter(reference=reference).first()
        if not booking:
            return Response({"detail": "Booking was not found."}, status=404)
        if not can_access_branch(request.user, booking.branch, self.required_branch_roles):
            return Response({"detail": "You are not assigned to this branch."}, status=403)
        serializer = BookingActionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        action = serializer.validated_data["action"]
        previous = booking.status
        if previous not in self.allowed_from[action]:
            return Response(
                {
                    "detail": (
                        f"{action.replace('_', ' ').title()} is not available "
                        f"while this booking is {booking.get_status_display()}."
                    )
                },
                status=400,
            )
        booking.status = self.transitions[action]
        booking.updated_by = request.user
        if action == "confirm_price":
            if booking.pricing_status != Booking.PricingStatus.ESTIMATE:
                return Response({"detail": "This booking already has a final price."}, status=400)
            booking.total_amount = serializer.validated_data["final_amount"]
            booking.pricing_status = Booking.PricingStatus.FINAL
        if action == "propose_time":
            booking.proposed_start = serializer.validated_data["proposed_start"]
            booking.proposed_expires_at = timezone.now() + timedelta(days=2)
        booking.save()
        if action == "confirm_price":
            issue_invoice_for_source(booking)
        BookingHistory.objects.create(
            booking=booking,
            action=action,
            from_status=previous,
            to_status=booking.status,
            reason=serializer.validated_data.get("reason", ""),
            actor=request.user,
            metadata=(
                {"proposed_start": booking.proposed_start.isoformat()}
                if booking.proposed_start
                else {}
            ),
        )
        email_events = {
            "confirm": "confirmed",
            "propose_time": "time_proposed",
            "cancel": "cancelled",
            "reject": "rejected",
        }
        if action in email_events:
            transaction.on_commit(
                lambda booking_id=booking.pk, event=email_events[action], updated=str(booking.updated_at): (
                    enqueue_email_job(
                        job_type="booking_update",
                        object_id=booking_id,
                        event=event,
                        unique_key=f"booking:{booking_id}:{event}:{updated}",
                    )
                )
            )
        if action == "confirm":
            transaction.on_commit(
                lambda booking_id=booking.pk: schedule_booking_reminders(
                    Booking.objects.get(pk=booking_id)
                )
            )
        return Response(BookingSerializer(booking_queryset().get(pk=booking.pk)).data)


class ManagementBookingBlockListCreateView(
    BranchAccessQuerysetMixin, generics.ListCreateAPIView
):
    serializer_class = BookingBlockSerializer
    permission_classes = [IsOwnerOrAssignedBranchStaff]
    required_branch_roles = (BranchStaffAssignment.Role.MANAGER, BranchStaffAssignment.Role.RECEPTIONIST)
    queryset = BookingBlock.objects.select_related("branch")

    def perform_create(self, serializer):
        branch = serializer.validated_data["branch"]
        if not can_access_branch(self.request.user, branch, self.required_branch_roles):
            raise PermissionDenied("You are not assigned to this branch.")
        serializer.save(created_by=self.request.user, updated_by=self.request.user)


class ManagementBookingBlockDetailView(
    BranchAccessQuerysetMixin, generics.RetrieveUpdateDestroyAPIView
):
    serializer_class = BookingBlockSerializer
    permission_classes = [IsOwnerOrAssignedBranchStaff]
    required_branch_roles = ManagementBookingBlockListCreateView.required_branch_roles
    queryset = BookingBlock.objects.select_related("branch")

    def perform_update(self, serializer):
        branch = serializer.validated_data.get("branch", serializer.instance.branch)
        if not can_access_branch(self.request.user, branch, self.required_branch_roles):
            raise PermissionDenied("You are not assigned to this branch.")
        serializer.save(updated_by=self.request.user)
