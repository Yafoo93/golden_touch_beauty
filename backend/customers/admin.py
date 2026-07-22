from django.contrib import admin

from .models import CustomerConsent


@admin.register(CustomerConsent)
class CustomerConsentAdmin(admin.ModelAdmin):
    list_display = (
        "user", "terms_version", "privacy_version",
        "marketing_consent", "terms_privacy_accepted_at",
    )
    list_filter = ("marketing_consent", "terms_version", "privacy_version")
    search_fields = ("user__full_name", "user__email", "user__phone_number")
    autocomplete_fields = ("user",)
    readonly_fields = ("id", "created_at", "updated_at")
