from django.contrib import admin

from .models import CustomerAddress, CustomerConsent


@admin.register(CustomerConsent)
class CustomerConsentAdmin(admin.ModelAdmin):
    list_display = (
        "user", "terms_version", "privacy_version",
        "marketing_consent", "photograph_consent", "terms_privacy_accepted_at",
    )
    list_filter = ("marketing_consent", "photograph_consent", "terms_version", "privacy_version")
    search_fields = ("user__full_name", "user__email", "user__phone_number")
    autocomplete_fields = ("user",)
    readonly_fields = ("id", "created_at", "updated_at")


@admin.register(CustomerAddress)
class CustomerAddressAdmin(admin.ModelAdmin):
    list_display = ("label", "customer", "address_type", "city", "region", "is_default_billing", "is_default_delivery")
    list_filter = ("address_type", "region", "is_default_billing", "is_default_delivery")
    search_fields = ("label", "customer__full_name", "customer__email", "recipient_phone", "address_line_1")
    autocomplete_fields = ("customer",)
    readonly_fields = ("id", "created_at", "updated_at")
