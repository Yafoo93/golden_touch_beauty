from rest_framework import serializers

from .models import Receipt


class ReceiptSerializer(serializers.ModelSerializer):
    branch_code = serializers.CharField(source="branch.code", read_only=True)
    branch_name = serializers.CharField(source="branch.name", read_only=True)
    branch_address = serializers.CharField(source="branch.address", read_only=True)
    payment_reference = serializers.CharField(
        source="payment.reference", read_only=True
    )
    payment_method = serializers.CharField(source="payment.method", read_only=True)
    provider = serializers.CharField(source="payment.provider", read_only=True)

    class Meta:
        model = Receipt
        fields = (
            "id",
            "reference",
            "payment_reference",
            "payment_method",
            "provider",
            "source_type",
            "source_reference",
            "branch_code",
            "branch_name",
            "branch_address",
            "recipient_name",
            "currency",
            "amount",
            "line_items",
            "issued_at",
            "created_at",
        )
        read_only_fields = fields
