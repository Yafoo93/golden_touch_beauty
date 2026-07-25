from django.contrib import admin

from .models import Booking, BookingBlock, BookingHistory, BookingServiceItem


class BookingServiceInline(admin.TabularInline):
    model = BookingServiceItem
    extra = 0
    readonly_fields = ("service_name", "option_name", "unit_price", "duration_minutes")


class BookingHistoryInline(admin.TabularInline):
    model = BookingHistory
    extra = 0
    readonly_fields = ("action", "from_status", "to_status", "reason", "actor", "metadata", "created_at")

    def has_add_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ("reference", "customer", "branch", "preferred_start", "status", "total_amount")
    list_filter = ("branch", "status", "payment_method", "source")
    search_fields = ("reference", "customer__email", "recipient_name", "recipient_phone")
    readonly_fields = ("reference", "client_request_id", "created_at", "updated_at")
    inlines = (BookingServiceInline, BookingHistoryInline)


@admin.register(BookingBlock)
class BookingBlockAdmin(admin.ModelAdmin):
    list_display = ("branch", "block_type", "starts_at", "ends_at", "is_active")
    list_filter = ("branch", "block_type", "is_active")
