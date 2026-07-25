from django.contrib import admin

from .models import Order, OrderItem, StockReservation


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = (
        "product_variant", "product_name", "variant_name", "sku",
        "unit_price", "quantity", "line_total",
    )


class StockReservationInline(admin.TabularInline):
    model = StockReservation
    extra = 0
    readonly_fields = (
        "order_item", "inventory", "quantity", "status", "expires_at",
        "released_at", "converted_at",
    )


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = (
        "reference", "customer", "branch", "fulfillment_method", "status",
        "total_amount", "reservation_expires_at", "created_at",
    )
    list_filter = ("status", "fulfillment_method", "branch")
    search_fields = ("reference", "customer__email", "recipient_phone")
    inlines = (OrderItemInline, StockReservationInline)


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ("order", "product_name", "variant_name", "quantity", "line_total")
    search_fields = ("order__reference", "product_name", "sku")


@admin.register(StockReservation)
class StockReservationAdmin(admin.ModelAdmin):
    list_display = ("order", "inventory", "quantity", "status", "expires_at")
    list_filter = ("status",)
