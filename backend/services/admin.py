from django.contrib import admin

from .models import Service, ServiceBranchAvailability, ServiceCategory, ServicePriceOption


@admin.register(ServiceCategory)
class ServiceCategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "display_order", "is_active")
    list_editable = ("display_order", "is_active")
    prepopulated_fields = {"slug": ("name",)}
    search_fields = ("name",)


class ServiceBranchAvailabilityInline(admin.TabularInline):
    model = ServiceBranchAvailability
    extra = 0


class ServicePriceOptionInline(admin.TabularInline):
    model = ServicePriceOption
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
        "is_featured",
        "is_published",
        "is_active",
    )
    list_filter = (
        "category",
        "is_featured",
        "is_published",
        "is_active",
        "is_clinic_service",
        "is_home_service",
    )
    search_fields = ("name", "short_description", "description")
    prepopulated_fields = {"slug": ("name",)}
    readonly_fields = ("id", "created_at", "updated_at")
    inlines = (ServiceBranchAvailabilityInline, ServicePriceOptionInline)


@admin.register(ServiceBranchAvailability)
class ServiceBranchAvailabilityAdmin(admin.ModelAdmin):
    list_display = ("service", "branch", "is_available")
    list_filter = ("branch", "is_available")
    search_fields = ("service__name", "branch__name")


@admin.register(ServicePriceOption)
class ServicePriceOptionAdmin(admin.ModelAdmin):
    list_display = ("name", "service", "price", "duration_minutes", "display_order", "is_active")
    list_filter = ("is_active",)
    search_fields = ("name", "service__name", "description")
