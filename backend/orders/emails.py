import logging
from html import escape

from django.conf import settings
from django.core.mail import send_mail
from django.utils import timezone


logger = logging.getLogger("golden_touch.notifications")


def _money(value):
    return f"GHS {value:,.2f}"


def send_order_confirmation_email(order) -> bool:
    """Send the customer a non-sensitive summary of a newly created order."""
    if not order.customer_id or not order.customer.email:
        return False

    items = list(order.items.all())
    confirmation_url = (
        f"{settings.FRONTEND_URL.rstrip('/')}/checkout/success"
        f"?order={order.reference}"
    )
    account_url = f"{settings.FRONTEND_URL.rstrip('/')}/account"
    fulfillment = (
        f"Pickup at {order.branch.name}"
        if order.fulfillment_method == order.FulfillmentMethod.PICKUP
        else f"Delivery from {order.branch.name}"
    )
    reservation_deadline = (
        timezone.localtime(order.reservation_expires_at).strftime(
            "%A, %d %B %Y at %I:%M %p"
        )
        if order.reservation_expires_at
        else "the reservation deadline shown in your account"
    )
    item_lines = [
        (
            f"- {item.product_name} ({item.variant_name}) x {item.quantity}: "
            f"{_money(item.line_total)}"
        )
        for item in items
    ]
    message = "\n".join(
        [
            f"Hello {order.customer.full_name},",
            "",
            "We received your Golden Touch product order.",
            f"Reference: {order.reference}",
            f"Fulfillment: {fulfillment}",
            "",
            "Items:",
            *item_lines,
            "",
            f"Subtotal: {_money(order.subtotal)}",
            f"Delivery fee: {_money(order.delivery_fee)}",
            f"Total: {_money(order.total_amount)}",
            f"Payment status: {order.payment_status.replace('_', ' ').title()}",
            "",
            f"Your stock is reserved until {reservation_deadline}.",
            (
                "This is an order confirmation, not a payment receipt. "
                "The order is only paid after payment has been verified."
            ),
            f"View this order: {confirmation_url}",
            f"View your account: {account_url}",
            "",
            "Golden Touch Beauty Centre",
        ]
    )
    item_rows = "".join(
        (
            "<tr>"
            f"<td style='padding:8px 0'>{escape(item.product_name)} "
            f"({escape(item.variant_name)}) &times; {item.quantity}</td>"
            f"<td style='padding:8px 0;text-align:right'>"
            f"{escape(_money(item.line_total))}</td>"
            "</tr>"
        )
        for item in items
    )
    html_message = f"""
    <div style="background:#080808;color:#f5f1e8;padding:32px;font-family:Arial,sans-serif">
      <div style="max-width:640px;margin:auto;background:#121212;border:1px solid #574111;padding:32px">
        <p style="color:#dfa824;letter-spacing:.12em;text-transform:uppercase">Golden Touch Beauty Centre</p>
        <h1 style="font-family:Georgia,serif">Order received</h1>
        <p>Hello {escape(order.customer.full_name)},</p>
        <p>We received your product order and temporarily reserved its stock.</p>
        <table style="width:100%;color:#f5f1e8;border-collapse:collapse">
          <tr><td style="padding:8px 0">Reference</td><td style="text-align:right;color:#ecc454">{escape(order.reference)}</td></tr>
          <tr><td style="padding:8px 0">Fulfillment</td><td style="text-align:right">{escape(fulfillment)}</td></tr>
          {item_rows}
          <tr><td style="padding:8px 0">Subtotal</td><td style="text-align:right">{escape(_money(order.subtotal))}</td></tr>
          <tr><td style="padding:8px 0">Delivery fee</td><td style="text-align:right">{escape(_money(order.delivery_fee))}</td></tr>
          <tr><td style="padding:12px 0;font-weight:bold">Total</td><td style="padding:12px 0;text-align:right;color:#ecc454;font-weight:bold">{escape(_money(order.total_amount))}</td></tr>
        </table>
        <p>Your stock is reserved until {escape(reservation_deadline)}.</p>
        <p style="margin-top:28px">
          <a href="{escape(confirmation_url)}" style="display:inline-block;background:#dfa824;color:#080808;padding:14px 20px;text-decoration:none;font-weight:bold">View order confirmation</a>
        </p>
        <p style="color:#aaa49a;font-size:13px">This confirms that the order was received. It is not a payment receipt, and private delivery notes are not included.</p>
      </div>
    </div>
    """

    try:
        send_mail(
            subject=f"Order received - {order.reference}",
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[order.customer.email],
            html_message=html_message,
            fail_silently=False,
        )
    except Exception:
        logger.exception(
            "order_confirmation_email_failed",
            extra={"order_reference": order.reference},
        )
        return False

    logger.info(
        "order_confirmation_email_sent",
        extra={"order_reference": order.reference},
    )
    return True


def send_order_status_email(order, event: str | None = None) -> bool:
    """Notify a customer after an authoritative order status transition."""
    if not order.customer_id or not order.customer.email:
        return False

    event = event or order.status
    messages = {
        "payment_under_review": (
            "Payment is being reviewed",
            "We received your payment information and are verifying it.",
        ),
        "paid": (
            "Payment confirmed",
            "Your payment has been verified and your order is now confirmed.",
        ),
        "processing": (
            "Order in progress",
            "Our team has started preparing your order.",
        ),
        "ready_for_pickup": (
            "Order ready for pickup",
            f"Your order is ready for pickup at {order.branch.name}.",
        ),
        "shipped": (
            "Order dispatched",
            "Your order has been dispatched for delivery.",
        ),
        "delivered": (
            "Order delivered",
            "Your order has been marked as delivered.",
        ),
        "cancelled": (
            "Order cancelled",
            "Your order has been cancelled. Please contact us if you need help.",
        ),
        "expired": (
            "Order reservation expired",
            (
                "The payment window ended before payment was verified, so the "
                "reserved stock has been released."
            ),
        ),
        "returned": (
            "Return received",
            "Your returned order has been received and is being reviewed.",
        ),
        "refunded": (
            "Order refunded",
            "The refund for your order has been recorded.",
        ),
    }
    if event not in messages:
        return False

    heading, update_text = messages[event]
    account_url = f"{settings.FRONTEND_URL.rstrip('/')}/account"
    item_lines = [
        f"- {item.product_name} ({item.variant_name}) x {item.quantity}"
        for item in order.items.all()
    ]
    customer_name = order.customer.full_name or "there"
    message = "\n".join(
        [
            f"Hello {customer_name},",
            "",
            update_text,
            f"Reference: {order.reference}",
            f"Status: {order.get_status_display()}",
            f"Branch: {order.branch.name}",
            "",
            "Items:",
            *item_lines,
            "",
            f"Order total: {_money(order.total_amount)}",
            f"View your order: {account_url}",
            "",
            "Golden Touch Beauty Centre",
        ]
    )
    item_rows = "".join(
        (
            "<tr>"
            f"<td style='padding:8px 0'>{escape(item.product_name)} "
            f"({escape(item.variant_name)}) &times; {item.quantity}</td>"
            "</tr>"
        )
        for item in order.items.all()
    )
    html_message = f"""
    <div style="background:#080808;color:#f5f1e8;padding:32px;font-family:Arial,sans-serif">
      <div style="max-width:640px;margin:auto;background:#121212;border:1px solid #574111;padding:32px">
        <p style="color:#dfa824;letter-spacing:.12em;text-transform:uppercase">Golden Touch Beauty Centre</p>
        <h1 style="font-family:Georgia,serif">{escape(heading)}</h1>
        <p>Hello {escape(customer_name)},</p>
        <p>{escape(update_text)}</p>
        <table style="width:100%;color:#f5f1e8;border-collapse:collapse">
          <tr><td style="padding:8px 0">Reference</td><td style="text-align:right;color:#ecc454">{escape(order.reference)}</td></tr>
          <tr><td style="padding:8px 0">Status</td><td style="text-align:right">{escape(order.get_status_display())}</td></tr>
          <tr><td style="padding:8px 0">Branch</td><td style="text-align:right">{escape(order.branch.name)}</td></tr>
          {item_rows}
          <tr><td style="padding:12px 0;font-weight:bold">Total</td><td style="padding:12px 0;text-align:right;color:#ecc454;font-weight:bold">{escape(_money(order.total_amount))}</td></tr>
        </table>
        <p style="margin-top:28px"><a href="{escape(account_url)}" style="display:inline-block;background:#dfa824;color:#080808;padding:14px 20px;text-decoration:none;font-weight:bold">View your orders</a></p>
        <p style="color:#aaa49a;font-size:13px">Private delivery instructions and contact details are not included in this email.</p>
      </div>
    </div>
    """
    try:
        send_mail(
            subject=f"{heading} - {order.reference}",
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[order.customer.email],
            html_message=html_message,
            fail_silently=False,
        )
    except Exception:
        logger.exception(
            "order_status_email_failed",
            extra={"order_reference": order.reference, "event": event},
        )
        return False

    logger.info(
        "order_status_email_sent",
        extra={"order_reference": order.reference, "event": event},
    )
    return True
