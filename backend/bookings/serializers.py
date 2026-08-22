import json
from datetime import datetime, timedelta
from decimal import Decimal

from django.db import transaction
from django.utils import timezone
from rest_framework import serializers

from accounts.models import User
from branches.models import Branch, BranchStaffAssignment
from branches.permissions import can_access_branch
from core.phone import is_international_phone_number, normalize_phone_number
from core.uploads import RestrictedImageField, validate_image_upload
from payments.services import issue_invoice_for_source
from services.models import Service, ServiceBranchAvailability, ServicePriceOption

from .models import Booking, BookingBlock, BookingHistory, BookingServiceItem


ACTIVE_BOOKING_STATUSES = {
    Booking.Status.PENDING,
    Booking.Status.CONFIRMED,
    Booking.Status.CHECKED_IN,
    Booking.Status.IN_PROGRESS,
    Booking.Status.PROPOSED,
    Booking.Status.RESCHEDULED,
}


class BookingServiceItemSerializer(serializers.ModelSerializer):
    service_id = serializers.UUIDField(read_only=True)
    price_option_id = serializers.UUIDField(read_only=True, allow_null=True)

    class Meta:
        model = BookingServiceItem
        fields = (
            "id", "service_id", "price_option_id", "service_name", "option_name",
            "unit_price", "duration_minutes",
        )


class BookingHistorySerializer(serializers.ModelSerializer):
    actor_name = serializers.CharField(source="actor.full_name", read_only=True, default="")

    class Meta:
        model = BookingHistory
        fields = (
            "id", "action", "from_status", "to_status", "reason", "actor_name",
            "metadata", "created_at",
        )


class CustomerBookingHistorySerializer(serializers.ModelSerializer):
    """Customer-safe history without internal reasons, metadata, or staff names."""

    class Meta:
        model = BookingHistory
        fields = (
            "id", "action", "from_status", "to_status", "created_at",
        )


class BookingSerializer(serializers.ModelSerializer):
    branch_code = serializers.CharField(source="branch.code", read_only=True)
    branch_name = serializers.CharField(source="branch.name", read_only=True)
    customer_name = serializers.CharField(source="customer.full_name", read_only=True)
    customer_email = serializers.CharField(source="customer.email", read_only=True)
    services = BookingServiceItemSerializer(source="service_items", many=True, read_only=True)
    history = BookingHistorySerializer(many=True, read_only=True)
    finishes_after_branch_closing = serializers.SerializerMethodField()
    can_view_sensitive_intake = serializers.SerializerMethodField()

    class Meta:
        model = Booking
        fields = (
            "id", "reference", "branch_code", "branch_name", "customer_name",
            "customer_email", "status", "source", "preferred_start",
            "proposed_start", "proposed_expires_at", "total_duration_minutes",
            "total_amount", "pricing_status", "recipient_is_customer", "recipient_name",
            "recipient_phone", "allergies", "conditions", "previous_treatments",
            "notes", "photo_marketing_consent", "payment_method",
            "payment_status", "finishes_after_branch_closing", "services",
            "history", "can_view_sensitive_intake", "created_at", "updated_at",
        )

    def get_can_view_sensitive_intake(self, booking):
        request = self.context.get("request")
        user = getattr(request, "user", None)
        if not user or not user.is_staff:
            return True
        return can_access_branch(
            user, booking.branch,
            required_roles=(BranchStaffAssignment.Role.MANAGER, BranchStaffAssignment.Role.SERVICE_PROVIDER),
        )

    def to_representation(self, instance):
        data = super().to_representation(instance)
        if not data["can_view_sensitive_intake"]:
            for field in ("allergies", "conditions", "previous_treatments", "notes"):
                data.pop(field, None)
        return data


    def get_finishes_after_branch_closing(self, booking):
        local_start = timezone.localtime(booking.preferred_start)
        closing = timezone.make_aware(
            datetime.combine(local_start.date(), booking.branch.closing_time),
            timezone.get_current_timezone(),
        )
        return (
            booking.preferred_start
            + timedelta(minutes=booking.total_duration_minutes)
            > closing
        )


class CustomerBookingSerializer(BookingSerializer):
    history = CustomerBookingHistorySerializer(many=True, read_only=True)


class BookingCreateSerializer(serializers.Serializer):
    client_request_id = serializers.UUIDField()
    branch_code = serializers.CharField(max_length=30)
    preferred_start = serializers.DateTimeField()
    service_selections = serializers.JSONField()
    recipient_is_customer = serializers.BooleanField(default=True)
    recipient_name = serializers.CharField(max_length=200)
    recipient_phone = serializers.CharField(max_length=30)
    allergies = serializers.CharField(required=False, allow_blank=True)
    conditions = serializers.CharField(required=False, allow_blank=True)
    previous_treatments = serializers.CharField(required=False, allow_blank=True)
    notes = serializers.CharField(required=False, allow_blank=True)
    treatment_photo = RestrictedImageField(required=False)
    photo_marketing_consent = serializers.BooleanField(default=False)
    payment_method = serializers.ChoiceField(choices=Booking.PaymentMethod.choices)
    source = serializers.ChoiceField(choices=Booking.Source.choices, default=Booking.Source.WEBSITE)
    customer_id = serializers.UUIDField(required=False)
    duplicate_override = serializers.BooleanField(default=False)
    duplicate_override_reason = serializers.CharField(required=False, allow_blank=True, max_length=300)

    def validate_treatment_photo(self, image):
        return validate_image_upload(image)

    def validate_recipient_phone(self, value):
        normalized = normalize_phone_number(value)
        if not is_international_phone_number(normalized):
            raise serializers.ValidationError("Enter a valid international phone number.")
        return normalized

    def validate_service_selections(self, value):
        if isinstance(value, str):
            try:
                value = json.loads(value)
            except json.JSONDecodeError as exc:
                raise serializers.ValidationError("Service selections must be valid JSON.") from exc
        if not isinstance(value, list) or not value:
            raise serializers.ValidationError("Select at least one service.")
        if len(value) > 20:
            raise serializers.ValidationError("A booking cannot exceed 20 services.")
        service_ids = [str(item.get("service_id", "")) for item in value if isinstance(item, dict)]
        if len(service_ids) != len(value) or len(service_ids) != len(set(service_ids)):
            raise serializers.ValidationError("Each selected service must appear once.")
        return value

    def validate(self, attrs):
        request = self.context["request"]
        user = request.user
        management = bool(user.is_staff or user.is_superuser)
        customer = user
        if attrs.get("customer_id"):
            if not management:
                raise serializers.ValidationError({"customer_id": "Only staff can book for another customer."})
            customer = User.objects.filter(pk=attrs["customer_id"], is_active=True).first()
            if not customer:
                raise serializers.ValidationError({"customer_id": "Customer was not found."})
        branch = Branch.objects.filter(code__iexact=attrs["branch_code"], is_active=True).first()
        if not branch:
            raise serializers.ValidationError({"branch_code": "Select an active branch."})
        if attrs["preferred_start"] <= timezone.now():
            raise serializers.ValidationError({"preferred_start": "Choose a future date and time."})

        service_ids = [item["service_id"] for item in attrs["service_selections"]]
        services = {
            str(service.id): service
            for service in Service.objects.filter(
                id__in=service_ids,
                is_active=True,
                is_published=True,
                category__is_active=True,
                branch_availability__branch=branch,
                branch_availability__is_available=True,
            ).prefetch_related("price_options")
        }
        if set(services) != set(map(str, service_ids)):
            raise serializers.ValidationError(
                {"service_selections": "One or more services are unavailable at this branch."}
            )
        resolved = []
        for selection in attrs["service_selections"]:
            service = services[str(selection["service_id"])]
            if service.price_type == Service.PriceType.QUOTATION:
                raise serializers.ValidationError({
                    "service_selections": f"Contact the selected branch for a price for {service.name}."
                })
            option = None
            if selection.get("price_option_id"):
                option = ServicePriceOption.objects.filter(
                    pk=selection["price_option_id"], service=service, is_active=True
                ).first()
                if not option:
                    raise serializers.ValidationError(
                        {"service_selections": f"Select a valid price option for {service.name}."}
                    )
            elif service.price_type == Service.PriceType.OPTIONS:
                raise serializers.ValidationError(
                    {"service_selections": f"Select a price option for {service.name}."}
                )
            price = option.price if option else service.price
            duration = option.duration_minutes if option and option.duration_minutes else service.duration_minutes
            resolved.append((service, option, price, duration))
        local_start = timezone.localtime(attrs["preferred_start"])
        if local_start.minute % 30 or local_start.second or local_start.microsecond:
            raise serializers.ValidationError(
                {"preferred_start": "Choose a time on a 30-minute interval."}
            )
        day_name = local_start.strftime("%A").lower()
        if day_name not in {str(day).lower() for day in branch.opening_days}:
            raise serializers.ValidationError(
                {"preferred_start": "The selected branch is closed on this date."}
            )
        opening = timezone.make_aware(
            datetime.combine(local_start.date(), branch.opening_time),
            timezone.get_current_timezone(),
        )
        closing = timezone.make_aware(
            datetime.combine(local_start.date(), branch.closing_time),
            timezone.get_current_timezone(),
        )
        finish = attrs["preferred_start"] + timedelta(
            minutes=sum(duration for _, _, _, duration in resolved)
        )
        if attrs["preferred_start"] < opening or attrs["preferred_start"] >= closing:
            raise serializers.ValidationError(
                {"preferred_start": "Choose a time within this branch's opening hours."}
            )
        if BookingBlock.objects.filter(
            branch=branch,
            is_active=True,
            starts_at__lt=finish,
            ends_at__gt=attrs["preferred_start"],
        ).exists():
            raise serializers.ValidationError(
                {"preferred_start": "This time is no longer available. Choose another time."}
            )
        if attrs["payment_method"] == Booking.PaymentMethod.CLINIC and any(
            not service.allows_pay_at_clinic for service, _, _, _ in resolved
        ):
            raise serializers.ValidationError(
                {"payment_method": "Pay at clinic is not available for every selected service."}
            )
        override = attrs.get("duplicate_override", False)
        if override and not management:
            raise serializers.ValidationError({"duplicate_override": "Only authorized staff can override duplicates."})
        if override and not attrs.get("duplicate_override_reason", "").strip():
            raise serializers.ValidationError(
                {"duplicate_override_reason": "Give an audited reason for the duplicate override."}
            )
        service_id_set = [service.id for service, _, _, _ in resolved]
        duplicate = Booking.objects.filter(
            customer=customer,
            status__in=ACTIVE_BOOKING_STATUSES,
            preferred_start__gt=timezone.now(),
            service_items__service_id__in=service_id_set,
        ).distinct().exists()
        if duplicate and not override:
            raise serializers.ValidationError(
                {"service_selections": "An active booking already contains one of these services."}
            )
        attrs["_customer"] = customer
        attrs["_branch"] = branch
        attrs["_resolved_services"] = resolved
        return attrs

    @transaction.atomic
    def create(self, validated_data):
        customer = validated_data.pop("_customer")
        branch = validated_data.pop("_branch")
        resolved = validated_data.pop("_resolved_services")
        validated_data.pop("branch_code")
        validated_data.pop("service_selections")
        validated_data.pop("customer_id", None)
        actor = self.context["request"].user
        total = sum((price for _, _, price, _ in resolved), Decimal("0.00"))
        duration = sum(duration for _, _, _, duration in resolved)
        booking = Booking.objects.create(
            branch=branch,
            customer=customer,
            total_amount=total,
            total_duration_minutes=duration,
            pricing_status=(
                Booking.PricingStatus.ESTIMATE
                if any(
                    service.price_type in {
                        Service.PriceType.STARTING_FROM,
                        Service.PriceType.RANGE,
                    }
                    for service, _, _, _ in resolved
                )
                else Booking.PricingStatus.FINAL
            ),
            created_by=actor,
            updated_by=actor,
            **validated_data,
        )
        BookingServiceItem.objects.bulk_create(
            [
                BookingServiceItem(
                    booking=booking,
                    service=service,
                    price_option=option,
                    service_name=service.name,
                    option_name=option.name if option else "",
                    unit_price=price,
                    duration_minutes=item_duration,
                )
                for service, option, price, item_duration in resolved
            ]
        )
        BookingHistory.objects.create(
            booking=booking,
            action="created",
            to_status=booking.status,
            actor=actor,
            metadata={"source": booking.source},
        )
        if booking.pricing_status == Booking.PricingStatus.FINAL:
            issue_invoice_for_source(booking)
        return booking


class BookingActionSerializer(serializers.Serializer):
    action = serializers.ChoiceField(
        choices=(
            "confirm", "reject", "cancel", "check_in", "start", "complete",
            "no_show", "propose_time", "confirm_price",
        )
    )
    reason = serializers.CharField(required=False, allow_blank=True)
    proposed_start = serializers.DateTimeField(required=False)
    final_amount = serializers.DecimalField(
        max_digits=12, decimal_places=2, min_value=0, required=False
    )

    def validate(self, attrs):
        action = attrs["action"]
        if action in {"reject", "cancel", "no_show"} and not attrs.get("reason", "").strip():
            raise serializers.ValidationError({"reason": "Give a reason for this action."})
        if action == "propose_time":
            proposed = attrs.get("proposed_start")
            if not proposed or proposed <= timezone.now():
                raise serializers.ValidationError({"proposed_start": "Choose a future proposed time."})
        if action == "confirm_price" and attrs.get("final_amount") is None:
            raise serializers.ValidationError({"final_amount": "Enter the confirmed final price."})
        return attrs


class BookingBlockSerializer(serializers.ModelSerializer):
    branch_code = serializers.SlugRelatedField(
        source="branch",
        slug_field="code",
        queryset=Branch.objects.filter(is_active=True),
    )
    branch_name = serializers.CharField(source="branch.name", read_only=True)

    class Meta:
        model = BookingBlock
        fields = (
            "id", "branch_code", "branch_name", "starts_at", "ends_at", "block_type", "reason",
            "is_active", "created_at",
        )
        read_only_fields = ("id", "created_at")

    def validate(self, attrs):
        starts = attrs.get("starts_at", getattr(self.instance, "starts_at", None))
        ends = attrs.get("ends_at", getattr(self.instance, "ends_at", None))
        if starts and ends and ends <= starts:
            raise serializers.ValidationError({"ends_at": "End time must be after start time."})
        return attrs
