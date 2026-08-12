from django.db import transaction
from rest_framework import serializers

from core.phone import is_international_phone_number, normalize_phone_number
from django.utils import timezone
from .models import CustomerAddress, CustomerConsent


class CustomerConsentSerializer(serializers.ModelSerializer):
    def update(self, instance, validated_data):
        now = timezone.now()
        if "marketing_consent" in validated_data and validated_data["marketing_consent"] != instance.marketing_consent:
            instance.marketing_consent_updated_at = now
        if "photograph_consent" in validated_data and validated_data["photograph_consent"] != instance.photograph_consent:
            instance.photograph_consent_updated_at = now
        for field, value in validated_data.items():
            setattr(instance, field, value)
        instance.save()
        return instance

    class Meta:
        model = CustomerConsent
        fields = (
            "marketing_consent", "marketing_consent_updated_at",
            "photograph_consent", "photograph_consent_updated_at",
            "terms_version", "privacy_version", "terms_privacy_accepted_at",
        )
        read_only_fields = (
            "marketing_consent_updated_at", "photograph_consent_updated_at",
            "terms_version", "privacy_version", "terms_privacy_accepted_at",
        )


class CustomerAddressSerializer(serializers.ModelSerializer):
    def validate_recipient_phone(self, value):
        normalized = normalize_phone_number(value)
        if not is_international_phone_number(normalized):
            raise serializers.ValidationError("Enter a valid international phone number.")
        return normalized

    def validate(self, attrs):
        address_type = attrs.get("address_type", self.instance.address_type if self.instance else CustomerAddress.AddressType.DELIVERY)
        billing = attrs.get("is_default_billing", self.instance.is_default_billing if self.instance else False)
        delivery = attrs.get("is_default_delivery", self.instance.is_default_delivery if self.instance else False)
        if billing and address_type not in (CustomerAddress.AddressType.BILLING, CustomerAddress.AddressType.BOTH):
            raise serializers.ValidationError({"is_default_billing": "A delivery-only address cannot be the billing default."})
        if delivery and address_type not in (CustomerAddress.AddressType.DELIVERY, CustomerAddress.AddressType.BOTH):
            raise serializers.ValidationError({"is_default_delivery": "A billing-only address cannot be the delivery default."})
        return attrs

    @transaction.atomic
    def save(self, **kwargs):
        customer = self.context["request"].user
        billing = self.validated_data.get("is_default_billing", self.instance.is_default_billing if self.instance else False)
        delivery = self.validated_data.get("is_default_delivery", self.instance.is_default_delivery if self.instance else False)
        current_pk = self.instance.pk if self.instance else None
        if billing:
            CustomerAddress.objects.filter(customer=customer, is_default_billing=True).exclude(pk=current_pk).update(is_default_billing=False)
        if delivery:
            CustomerAddress.objects.filter(customer=customer, is_default_delivery=True).exclude(pk=current_pk).update(is_default_delivery=False)
        return super().save(customer=customer, **kwargs)

    class Meta:
        model = CustomerAddress
        fields = ("id", "label", "address_type", "recipient_name", "recipient_phone", "address_line_1", "address_line_2", "city", "region", "landmark", "country", "is_default_billing", "is_default_delivery", "created_at", "updated_at")
        read_only_fields = ("id", "created_at", "updated_at")
