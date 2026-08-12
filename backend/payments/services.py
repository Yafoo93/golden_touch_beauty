from decimal import Decimal

from django.db import transaction
from notifications.jobs import enqueue_email_job

from .models import Invoice, Payment, Receipt


def _invoice_snapshot(source):
    model_name = source._meta.model_name
    if model_name == "order":
        items = [
            {
                "description": f"{item.product_name} ({item.variant_name})",
                "quantity": item.quantity,
                "unit_price": str(item.unit_price),
                "line_total": str(item.line_total),
            }
            for item in source.items.all()
        ]
        return "order", source.subtotal, source.total_amount, items
    if model_name == "booking":
        items = [
            {
                "description": (
                    f"{item.service_name}"
                    f"{f' ({item.option_name})' if item.option_name else ''}"
                ),
                "quantity": 1,
                "unit_price": str(item.unit_price),
                "line_total": str(item.unit_price),
            }
            for item in source.service_items.all()
        ]
        return "booking", source.total_amount, source.total_amount, items
    raise ValueError("An invoice can only be issued for an order or booking.")


@transaction.atomic
def issue_invoice_for_source(source):
    """Create one immutable financial snapshot for a booking or order."""
    source_type, subtotal, total_amount, line_items = _invoice_snapshot(source)
    customer = source.customer
    if not customer:
        raise ValueError("An invoice source must have a customer.")
    source_field = {source_type: source}
    due_at = (
        source.reservation_expires_at
        if source_type == "order"
        else source.preferred_start
    )
    invoice, _ = Invoice.objects.get_or_create(
        **source_field,
        defaults={
            "branch": source.branch,
            "customer": customer,
            "source_type": source_type,
            "source_reference": source.reference,
            "recipient_name": customer.full_name,
            "recipient_email": customer.email,
            "currency": source.currency if source_type == "order" else "GHS",
            "subtotal": subtotal,
            "total_amount": total_amount,
            "line_items": line_items,
            "due_at": due_at,
        },
    )
    return invoice


def _source_snapshot(payment):
    if payment.order_id:
        source = payment.order
        items = [
            {
                "description": f"{item.product_name} ({item.variant_name})",
                "quantity": item.quantity,
                "unit_price": str(item.unit_price),
                "line_total": str(item.line_total),
            }
            for item in source.items.all()
        ]
        return "order", source.reference, source.total_amount, items
    if payment.booking_id:
        source = payment.booking
        items = [
            {
                "description": (
                    f"{item.service_name}"
                    f"{f' ({item.option_name})' if item.option_name else ''}"
                ),
                "quantity": 1,
                "unit_price": str(item.unit_price),
                "line_total": str(item.unit_price),
            }
            for item in source.service_items.all()
        ]
        return "booking", source.reference, source.total_amount, items
    raise ValueError("A verified payment must be allocated to an order or booking.")


@transaction.atomic
def issue_receipt_for_verified_payment(payment):
    """Create one immutable receipt after authoritative payment verification."""
    payment = (
        Payment.objects.select_for_update()
        .select_related("customer", "branch", "order", "booking")
        .get(pk=payment.pk)
    )
    if payment.status != Payment.Status.SUCCEEDED or not payment.paid_at:
        raise ValueError("A receipt can only be issued for a verified payment.")
    if not payment.customer_id:
        raise ValueError("The verified payment has no customer.")

    source_type, source_reference, expected_amount, line_items = _source_snapshot(
        payment
    )
    if Decimal(payment.amount) != Decimal(expected_amount):
        raise ValueError("The verified payment amount does not match its source.")

    receipt, created = Receipt.objects.get_or_create(
        payment=payment,
        defaults={
            "branch": payment.branch,
            "customer": payment.customer,
            "source_type": source_type,
            "source_reference": source_reference,
            "recipient_name": payment.customer.full_name,
            "recipient_email": payment.customer.email,
            "currency": payment.currency,
            "amount": payment.amount,
            "line_items": line_items,
            "issued_at": payment.paid_at,
        },
    )
    source = payment.order if payment.order_id else payment.booking
    invoice = issue_invoice_for_source(source)
    if invoice.status != Invoice.Status.PAID or invoice.paid_at != payment.paid_at:
        invoice.status = Invoice.Status.PAID
        invoice.paid_at = payment.paid_at
        invoice.save(update_fields=["status", "paid_at", "updated_at"])
    if created or not receipt.email_sent_at:
        transaction.on_commit(
            lambda receipt_id=receipt.pk: enqueue_email_job(
                job_type="payment_receipt",
                object_id=receipt_id,
                unique_key=f"receipt:{receipt_id}:email",
            )
        )
    return receipt
