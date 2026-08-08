from decimal import Decimal

from django.db import transaction

from .emails import send_receipt_email
from .models import Payment, Receipt


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
    if created or not receipt.email_sent_at:
        transaction.on_commit(
            lambda receipt_id=receipt.pk: send_receipt_email(
                Receipt.objects.select_related("payment", "branch").get(
                    pk=receipt_id
                )
            )
        )
    return receipt
