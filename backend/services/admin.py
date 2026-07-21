from django.contrib import admin

from .models import Service, ServiceBranchAvailability, ServiceCategory


@admin.register(ServiceCategory)
class ServiceCategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "display_order", "is_active")
    list_editable = ("display_order", "is_active")
    prepopulated_fields = {"slug": ("name",)}
    search_fields = ("name",)


class ServiceBranchAvailabilityInline(admin.TabularInline):
    model = ServiceBranchAvailability
    extra = 0


@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "category",
        "price",
        "duration_minutes",
        "requires_full_payment",
        "allows_pay_at_clinic",
        "is_published",
        "is_active",
    )
    list_filter = (
        "category",
        "is_published",
        "is_active",
        "is_clinic_service",
        "is_home_service",
    )
    search_fields = ("name", "short_description", "description")
    prepopulated_fields = {"slug": ("name",)}
    readonly_fields = ("id", "created_at", "updated_at")
    inlines = (ServiceBranchAvailabilityInline,)


@admin.register(ServiceBranchAvailability)
class ServiceBranchAvailabilityAdmin(admin.ModelAdmin):
    list_display = ("service", "branch", "is_available")
    list_filter = ("branch", "is_available")
    search_fields = ("service__name", "branch__name")
