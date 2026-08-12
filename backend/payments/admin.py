from django.contrib import admin
from django.contrib import messages

from .models import Invoice, Payment, Receipt
from .services import issue_receipt_for_verified_payment


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = (
        "reference",
        "customer",
        "branch",
        "provider",
        "status",
        "amount",
        "currency",
        "paid_at",
    )
    list_filter = ("status", "provider", "branch")
    search_fields = (
        "reference",
        "provider_reference",
        "customer__email",
        "customer__phone_number",
    )
    readonly_fields = ("reference", "created_at", "updated_at")
    actions = ("issue_verified_receipts",)

    @admin.action(description="Issue receipts for selected verified payments")
    def issue_verified_receipts(self, request, queryset):
        issued = 0
        for payment in queryset:
            try:
                issue_receipt_for_verified_payment(payment)
            except ValueError as exc:
                self.message_user(
                    request,
                    f"{payment.reference}: {exc}",
                    level=messages.ERROR,
                )
            else:
                issued += 1
        if issued:
            self.message_user(
                request,
                f"{issued} verified payment receipt(s) issued.",
                level=messages.SUCCESS,
            )


@admin.register(Receipt)
class ReceiptAdmin(admin.ModelAdmin):
    list_display = (
        "reference",
        "customer",
        "branch",
        "source_type",
        "source_reference",
        "amount",
        "issued_at",
        "email_sent_at",
    )
    list_filter = ("source_type", "branch")
    search_fields = (
        "reference",
        "payment__reference",
        "source_reference",
        "customer__email",
    )
    readonly_fields = (
        "reference",
        "payment",
        "customer",
        "branch",
        "source_type",
        "source_reference",
        "recipient_name",
        "recipient_email",
        "currency",
        "amount",
        "line_items",
        "issued_at",
        "email_sent_at",
        "created_at",
        "updated_at",
    )


@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = (
        "reference",
        "customer",
        "branch",
        "source_type",
        "source_reference",
        "status",
        "total_amount",
        "issued_at",
    )
    list_filter = ("status", "source_type", "branch")
    search_fields = (
        "reference",
        "source_reference",
        "customer__email",
        "customer__phone_number",
    )
    readonly_fields = (
        "reference",
        "customer",
        "branch",
        "booking",
        "order",
        "source_type",
        "source_reference",
        "recipient_name",
        "recipient_email",
        "currency",
        "subtotal",
        "total_amount",
        "line_items",
        "issued_at",
        "due_at",
        "created_at",
        "updated_at",
    )
