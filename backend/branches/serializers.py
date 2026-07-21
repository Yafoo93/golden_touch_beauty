from rest_framework import serializers

from .models import Branch


class PublicBranchSerializer(serializers.ModelSerializer):
    class Meta:
        model = Branch
        fields = (
            "id",
            "code",
            "name",
            "address",
            "telephone_number",
            "secondary_telephone_number",
            "whatsapp_number",
            "secondary_whatsapp_number",
            "email",
            "google_maps_url",
            "opening_days",
            "opening_time",
            "closing_time",
        )
        read_only_fields = fields


class PickupItemSerializer(serializers.Serializer):
    variant_id = serializers.UUIDField(required=False)
    sku = serializers.CharField(max_length=80, required=False)
    quantity = serializers.IntegerField(min_value=1, max_value=999)

    def validate(self, attrs):
        if bool(attrs.get("variant_id")) == bool(attrs.get("sku")):
            raise serializers.ValidationError(
                "Provide exactly one of variant_id or sku."
            )
        return attrs


class PickupOptionsRequestSerializer(serializers.Serializer):
    items = PickupItemSerializer(many=True, allow_empty=False)
