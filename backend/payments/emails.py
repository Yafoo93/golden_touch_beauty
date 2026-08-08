import logging
from decimal import Decimal
from html import escape

from django.conf import settings
from django.core.mail import send_mail
from django.utils import timezone


logger = logging.getLogger("golden_touch.notifications")


def _money(currency, value):
    return f"{currency} {Decimal(str(value)):,.2f}"


def send_receipt_email(receipt) -> bool:
    if receipt.email_sent_at or not receipt.recipient_email:
        return False

    receipt_url = (
        f"{settings.FRONTEND_URL.rstrip('/')}/account/receipts/"
        f"{receipt.reference}"
    )
    item_lines = [
        f"- {item['description']} x {item['quantity']}: "
        f"{_money(receipt.currency, item['line_total'])}"
        for item in receipt.line_items
    ]
    message = "\n".join(
        [
            f"Hello {receipt.recipient_name},",
            "",
            "Your Golden Touch payment was verified.",
            f"Receipt: {receipt.reference}",
            f"Payment reference: {receipt.payment.reference}",
            f"For: {receipt.source_type.title()} {receipt.source_reference}",
            f"Branch: {receipt.branch.name}",
            "",
            *item_lines,
            "",
            f"Amount paid: {_money(receipt.currency, receipt.amount)}",
            f"Paid at: {timezone.localtime(receipt.issued_at):%d %B %Y, %I:%M %p}",
            f"View or print your receipt: {receipt_url}",
            "",
            "Golden Touch Beauty Centre",
        ]
    )
    rows = "".join(
        "<tr>"
        f"<td style='padding:8px 0'>{escape(str(item['description']))} "
        f"&times; {item['quantity']}</td>"
        f"<td style='padding:8px 0;text-align:right'>"
        f"{escape(_money(receipt.currency, item['line_total']))}</td>"
        "</tr>"
        for item in receipt.line_items
    )
    html_message = f"""
    <div style="background:#080808;color:#f5f1e8;padding:32px;font-family:Arial,sans-serif">
      <div style="max-width:640px;margin:auto;background:#121212;border:1px solid #574111;padding:32px">
        <p style="color:#dfa824;letter-spacing:.12em;text-transform:uppercase">Golden Touch Beauty Centre</p>
        <h1 style="font-family:Georgia,serif">Payment receipt</h1>
        <p>Hello {escape(receipt.recipient_name)}, your payment was verified successfully.</p>
        <table style="width:100%;color:#f5f1e8;border-collapse:collapse">
          <tr><td style="padding:8px 0">Receipt</td><td style="text-align:right;color:#ecc454">{escape(receipt.reference)}</td></tr>
          <tr><td style="padding:8px 0">Payment</td><td style="text-align:right">{escape(receipt.payment.reference)}</td></tr>
          <tr><td style="padding:8px 0">Branch</td><td style="text-align:right">{escape(receipt.branch.name)}</td></tr>
          {rows}
          <tr><td style="padding:12px 0;font-weight:bold">Amount paid</td><td style="padding:12px 0;text-align:right;color:#ecc454;font-weight:bold">{escape(_money(receipt.currency, receipt.amount))}</td></tr>
        </table>
        <p style="margin-top:28px"><a href="{escape(receipt_url)}" style="display:inline-block;background:#dfa824;color:#080808;padding:14px 20px;text-decoration:none;font-weight:bold">View payment receipt</a></p>
      </div>
    </div>
    """
    try:
        send_mail(
            subject=f"Payment receipt - {receipt.reference}",
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[receipt.recipient_email],
            html_message=html_message,
            fail_silently=False,
        )
    except Exception:
        logger.exception(
            "payment_receipt_email_failed",
            extra={"receipt_reference": receipt.reference},
        )
        return False

    receipt.email_sent_at = timezone.now()
    receipt.save(update_fields=["email_sent_at", "updated_at"])
    logger.info(
        "payment_receipt_email_sent",
        extra={"receipt_reference": receipt.reference},
    )
    return True
