from django.contrib import admin
from django.contrib import messages

from .models import Order, OrderItem, StockReservation
from .services import transition_order_status


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
    readonly_fields = (
        "reference", "status", "payment_status", "paid_at", "cancelled_at",
        "created_at", "updated_at",
    )
    inlines = (OrderItemInline, StockReservationInline)
    actions = (
        "mark_processing",
        "mark_ready_for_pickup",
        "mark_shipped",
        "mark_delivered",
        "mark_returned",
    )

    def _transition_selected(self, request, queryset, new_status):
        changed = 0
        rejected = []
        for order in queryset:
            try:
                previous_status = order.status
                transition_order_status(order, new_status, actor=request.user)
                if previous_status != new_status:
                    changed += 1
            except ValueError as error:
                rejected.append(f"{order.reference}: {error}")
        if changed:
            self.message_user(
                request,
                f"Updated {changed} order(s); customer messages were queued.",
                messages.SUCCESS,
            )
        if rejected:
            self.message_user(request, " ".join(rejected), messages.WARNING)

    @admin.action(description="Move selected orders to processing")
    def mark_processing(self, request, queryset):
        self._transition_selected(request, queryset, Order.Status.PROCESSING)

    @admin.action(description="Mark selected pickup orders ready")
    def mark_ready_for_pickup(self, request, queryset):
        self._transition_selected(
            request, queryset, Order.Status.READY_FOR_PICKUP
        )

    @admin.action(description="Mark selected delivery orders shipped")
    def mark_shipped(self, request, queryset):
        self._transition_selected(request, queryset, Order.Status.SHIPPED)

    @admin.action(description="Mark selected orders delivered")
    def mark_delivered(self, request, queryset):
        self._transition_selected(request, queryset, Order.Status.DELIVERED)

    @admin.action(description="Mark selected delivered orders returned")
    def mark_returned(self, request, queryset):
        self._transition_selected(request, queryset, Order.Status.RETURNED)


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ("order", "product_name", "variant_name", "quantity", "line_total")
    search_fields = ("order__reference", "product_name", "sku")


@admin.register(StockReservation)
class StockReservationAdmin(admin.ModelAdmin):
    list_display = ("order", "inventory", "quantity", "status", "expires_at")
    list_filter = ("status",)
