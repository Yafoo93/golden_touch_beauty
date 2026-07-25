from rest_framework import serializers

from branches.models import Branch
from core.phone import is_international_phone_number, normalize_phone_number

from .models import Order, OrderItem, StockReservation


class OrderItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderItem
        fields = (
            "id", "product_name", "product_slug", "variant_name", "sku",
            "image_path", "unit_price", "quantity", "line_total",
        )


class StockReservationSerializer(serializers.ModelSerializer):
    class Meta:
        model = StockReservation
        fields = ("status", "quantity", "expires_at")


class OrderSerializer(serializers.ModelSerializer):
    branch_code = serializers.CharField(source="branch.code", read_only=True)
    branch_name = serializers.CharField(source="branch.name", read_only=True)
    items = OrderItemSerializer(many=True, read_only=True)

    class Meta:
        model = Order
        fields = (
            "id", "reference", "status", "payment_status",
            "fulfillment_method", "branch_code", "branch_name", "currency",
            "subtotal", "delivery_fee", "total_amount", "recipient_name",
            "recipient_phone", "delivery_address", "delivery_city",
            "delivery_notes", "reservation_expires_at", "paid_at",
            "cancelled_at", "items", "created_at",
        )


class CheckoutCreateSerializer(serializers.Serializer):
    client_request_id = serializers.UUIDField()
    fulfillment_method = serializers.ChoiceField(
        choices=Order.FulfillmentMethod.choices
    )
    pickup_branch_code = serializers.CharField(
        max_length=30, required=False, allow_blank=True
    )
    recipient_name = serializers.CharField(max_length=200)
    recipient_phone = serializers.CharField(max_length=30)
    delivery_address = serializers.CharField(
        required=False, allow_blank=True, max_length=1000
    )
    delivery_city = serializers.CharField(
        required=False, allow_blank=True, max_length=120
    )
    delivery_notes = serializers.CharField(
        required=False, allow_blank=True, max_length=1000
    )

    def validate_recipient_phone(self, value):
        normalized = normalize_phone_number(value)
        if not is_international_phone_number(normalized):
            raise serializers.ValidationError(
                "Enter a valid international phone number."
            )
        return normalized

    def validate(self, attrs):
        if attrs["fulfillment_method"] == Order.FulfillmentMethod.PICKUP:
            code = attrs.get("pickup_branch_code", "").strip()
            branch = Branch.objects.filter(code__iexact=code, is_active=True).first()
            if not branch:
                raise serializers.ValidationError(
                    {"pickup_branch_code": "Select an eligible pickup branch."}
                )
            attrs["_requested_branch"] = branch
        else:
            if not attrs.get("delivery_address", "").strip():
                raise serializers.ValidationError(
                    {"delivery_address": "Enter the delivery address."}
                )
            if not attrs.get("delivery_city", "").strip():
                raise serializers.ValidationError(
                    {"delivery_city": "Enter the delivery city or area."}
                )
            attrs["_requested_branch"] = None
            attrs["pickup_branch_code"] = ""
        return attrs
