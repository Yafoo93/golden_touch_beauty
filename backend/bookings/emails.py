import logging
from html import escape

from django.conf import settings
from django.core.mail import send_mail
from django.utils import timezone

from notifications.models import Notification
from notifications.services import create_notification


logger = logging.getLogger("golden_touch.notifications")


def _money(value):
    return f"GHS {value:,.2f}"


def send_booking_confirmation_email(booking) -> bool:
    """Send a non-sensitive summary after a booking request is created."""
    if not booking.customer_id:
        return False

    create_notification(
        recipient=booking.customer,
        category=Notification.Category.BOOKING,
        title="Booking request received",
        message=(
            f"Your booking request {booking.reference} was received and is "
            "waiting for branch confirmation."
        ),
        action_url=f"/account/appointments/{booking.reference}",
        event_key=f"booking:{booking.pk}:created",
    )
    if not booking.customer.email:
        return False

    items = list(booking.service_items.all())
    requested_time = timezone.localtime(booking.preferred_start)
    confirmation_url = (
        f"{settings.FRONTEND_URL.rstrip('/')}/book/confirmation/"
        f"{booking.reference}"
    )
    account_url = f"{settings.FRONTEND_URL.rstrip('/')}/account"
    service_lines = [
        (
            f"- {item.service_name}"
            f"{f' ({item.option_name})' if item.option_name else ''}: "
            f"{_money(item.unit_price)}, {item.duration_minutes} minutes"
        )
        for item in items
    ]
    payment_label = booking.get_payment_method_display()
    estimated = booking.pricing_status == booking.PricingStatus.ESTIMATE
    message = "\n".join(
        [
            f"Hello {booking.customer.full_name},",
            "",
            "We received your Golden Touch booking request.",
            f"Reference: {booking.reference}",
            f"Branch: {booking.branch.name}",
            f"Preferred date and time: {requested_time:%A, %d %B %Y at %I:%M %p}",
            "",
            "Services:",
            *service_lines,
            "",
            f"{'Starting estimate' if estimated else 'Total'}: {_money(booking.total_amount)}",
            f"Payment choice: {payment_label}",
            "",
            (
                "Your request is pending branch review. We will confirm the time "
                "or contact you with a suitable alternative."
            ),
            f"View this request: {confirmation_url}",
            f"View your account: {account_url}",
            "",
            "Golden Touch Beauty Centre",
        ]
    )
    service_rows = "".join(
        (
            "<tr>"
            f"<td style='padding:8px 0'>{escape(item.service_name)}"
            f"{f' ({escape(item.option_name)})' if item.option_name else ''}</td>"
            f"<td style='padding:8px 0;text-align:right'>{escape(_money(item.unit_price))}</td>"
            "</tr>"
        )
        for item in items
    )
    html_message = f"""
    <div style="background:#080808;color:#f5f1e8;padding:32px;font-family:Arial,sans-serif">
      <div style="max-width:640px;margin:auto;background:#121212;border:1px solid #574111;padding:32px">
        <p style="color:#dfa824;letter-spacing:.12em;text-transform:uppercase">Golden Touch Beauty Centre</p>
        <h1 style="font-family:Georgia,serif">Booking request received</h1>
        <p>Hello {escape(booking.customer.full_name)},</p>
        <p>We received your request. The branch will confirm the time or contact you with an alternative.</p>
        <table style="width:100%;color:#f5f1e8;border-collapse:collapse">
          <tr><td style="padding:8px 0">Reference</td><td style="text-align:right;color:#ecc454">{escape(booking.reference)}</td></tr>
          <tr><td style="padding:8px 0">Branch</td><td style="text-align:right">{escape(booking.branch.name)}</td></tr>
          <tr><td style="padding:8px 0">Preferred time</td><td style="text-align:right">{escape(requested_time.strftime('%d %B %Y, %I:%M %p'))}</td></tr>
          {service_rows}
          <tr><td style="padding:12px 0;font-weight:bold">{"Starting estimate" if estimated else "Total"}</td><td style="padding:12px 0;text-align:right;color:#ecc454;font-weight:bold">{escape(_money(booking.total_amount))}</td></tr>
          <tr><td style="padding:8px 0">Payment choice</td><td style="text-align:right">{escape(payment_label)}</td></tr>
        </table>
        <p style="margin-top:28px">
          <a href="{escape(confirmation_url)}" style="display:inline-block;background:#dfa824;color:#080808;padding:14px 20px;text-decoration:none;font-weight:bold">View booking request</a>
        </p>
        <p style="color:#aaa49a;font-size:13px">{"Management will assess the service and confirm the final amount before payment is requested. " if estimated else ""}This email does not include private treatment notes or medical information.</p>
      </div>
    </div>
    """

    try:
        send_mail(
            subject=f"Booking request received – {booking.reference}",
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[booking.customer.email],
            html_message=html_message,
            fail_silently=False,
        )
    except Exception:
        logger.exception(
            "booking_confirmation_email_failed",
            extra={"booking_reference": booking.reference},
        )
        return False

    logger.info(
        "booking_confirmation_email_sent",
        extra={"booking_reference": booking.reference},
    )
    return True


def send_booking_update_email(booking, event: str) -> bool:
    """Send a safe operational message after an appointment status change."""
    if not booking.customer_id:
        return False

    current_time = timezone.localtime(booking.preferred_start)
    proposed_time = (
        timezone.localtime(booking.proposed_start)
        if booking.proposed_start
        else None
    )
    account_url = f"{settings.FRONTEND_URL.rstrip('/')}/account"
    booking_url = (
        f"{settings.FRONTEND_URL.rstrip('/')}/book/confirmation/"
        f"{booking.reference}"
    )
    messages = {
        "confirmed": (
            "Appointment confirmed",
            (
                "Your appointment has been confirmed for "
                f"{current_time:%A, %d %B %Y at %I:%M %p}."
            ),
        ),
        "time_proposed": (
            "New appointment time proposed",
            (
                "The branch proposed a new appointment time: "
                f"{proposed_time:%A, %d %B %Y at %I:%M %p}. "
                "Sign in to accept or decline it."
                if proposed_time
                else "The branch proposed a new appointment time."
            ),
        ),
        "proposed_time_accepted": (
            "New appointment time confirmed",
            (
                "Your accepted appointment time is now confirmed for "
                f"{current_time:%A, %d %B %Y at %I:%M %p}."
            ),
        ),
        "cancelled": (
            "Appointment cancelled",
            (
                "Your appointment request has been cancelled. "
                "Contact the branch if you need help arranging another time."
            ),
        ),
        "rejected": (
            "Appointment request update",
            (
                "The branch could not accept this appointment request. "
                "Please book another available time or contact the branch."
            ),
        ),
    }
    if event not in messages:
        return False
    heading, update_text = messages[event]
    create_notification(
        recipient=booking.customer,
        category=Notification.Category.BOOKING,
        title=heading,
        message=f"{update_text} Reference: {booking.reference}.",
        action_url=f"/account/appointments/{booking.reference}",
        event_key=(
            f"booking:{booking.pk}:{event}:"
            f"{booking.updated_at.isoformat()}"
        ),
    )
    if not booking.customer.email:
        return False
    message = "\n".join(
        [
            f"Hello {booking.customer.full_name},",
            "",
            update_text,
            f"Reference: {booking.reference}",
            f"Branch: {booking.branch.name}",
            f"Current status: {booking.get_status_display()}",
            f"View booking: {booking_url}",
            f"View your account: {account_url}",
            "",
            "Golden Touch Beauty Centre",
        ]
    )
    html_message = f"""
    <div style="background:#080808;color:#f5f1e8;padding:32px;font-family:Arial,sans-serif">
      <div style="max-width:640px;margin:auto;background:#121212;border:1px solid #574111;padding:32px">
        <p style="color:#dfa824;letter-spacing:.12em;text-transform:uppercase">Golden Touch Beauty Centre</p>
        <h1 style="font-family:Georgia,serif">{escape(heading)}</h1>
        <p>Hello {escape(booking.customer.full_name)},</p>
        <p>{escape(update_text)}</p>
        <table style="width:100%;color:#f5f1e8;border-collapse:collapse">
          <tr><td style="padding:8px 0">Reference</td><td style="text-align:right;color:#ecc454">{escape(booking.reference)}</td></tr>
          <tr><td style="padding:8px 0">Branch</td><td style="text-align:right">{escape(booking.branch.name)}</td></tr>
          <tr><td style="padding:8px 0">Status</td><td style="text-align:right">{escape(booking.get_status_display())}</td></tr>
        </table>
        <p style="margin-top:28px"><a href="{escape(booking_url)}" style="display:inline-block;background:#dfa824;color:#080808;padding:14px 20px;text-decoration:none;font-weight:bold">View booking</a></p>
        <p style="color:#aaa49a;font-size:13px">Private treatment notes and medical information are never included in this email.</p>
      </div>
    </div>
    """
    try:
        send_mail(
            subject=f"{heading} - {booking.reference}",
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[booking.customer.email],
            html_message=html_message,
            fail_silently=False,
        )
    except Exception:
        logger.exception(
            "booking_update_email_failed",
            extra={"booking_reference": booking.reference, "event": event},
        )
        return False

    logger.info(
        "booking_update_email_sent",
        extra={"booking_reference": booking.reference, "event": event},
    )
    return True


def send_booking_reminder_email(
    booking, *, hours_before: int, scheduled_start: str
) -> bool:
    """Deliver one reminder unless its appointment is no longer eligible."""
    eligible_statuses = {booking.Status.CONFIRMED, booking.Status.RESCHEDULED}
    if (
        not booking.customer_id
        or booking.status not in eligible_statuses
        or booking.preferred_start.isoformat() != scheduled_start
        or booking.preferred_start <= timezone.now()
    ):
        return True

    appointment_time = timezone.localtime(booking.preferred_start)
    heading = f"Appointment reminder: {hours_before} hours to go"
    reminder_text = (
        f"Your appointment at {booking.branch.name} is scheduled for "
        f"{appointment_time:%A, %d %B %Y at %I:%M %p}."
    )
    booking_url = (
        f"{settings.FRONTEND_URL.rstrip('/')}/book/confirmation/"
        f"{booking.reference}"
    )
    event_suffix = f"{hours_before}:{scheduled_start}"
    create_notification(
        recipient=booking.customer,
        category=Notification.Category.BOOKING,
        title=heading,
        message=f"{reminder_text} Reference: {booking.reference}.",
        action_url=f"/account/appointments/{booking.reference}",
        event_key=f"booking:{booking.pk}:reminder:{event_suffix}",
    )
    if not booking.customer.email:
        return True

    message = "\n".join(
        [
            f"Hello {booking.customer.full_name},",
            "",
            reminder_text,
            f"Reference: {booking.reference}",
            f"View booking: {booking_url}",
            "",
            "Golden Touch Beauty Centre",
        ]
    )
    html_message = f"""
    <div style="background:#080808;color:#f5f1e8;padding:32px;font-family:Arial,sans-serif">
      <div style="max-width:640px;margin:auto;background:#121212;border:1px solid #574111;padding:32px">
        <p style="color:#dfa824;letter-spacing:.12em;text-transform:uppercase">Golden Touch Beauty Centre</p>
        <h1 style="font-family:Georgia,serif">{escape(heading)}</h1>
        <p>Hello {escape(booking.customer.full_name)},</p>
        <p>{escape(reminder_text)}</p>
        <p>Reference: <strong>{escape(booking.reference)}</strong></p>
        <p style="margin-top:28px"><a href="{escape(booking_url)}" style="display:inline-block;background:#dfa824;color:#080808;padding:14px 20px;text-decoration:none;font-weight:bold">View appointment</a></p>
      </div>
    </div>
    """
    send_mail(
        subject=f"{heading} - {booking.reference}",
        message=message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[booking.customer.email],
        html_message=html_message,
        fail_silently=False,
    )
    logger.info(
        "booking_reminder_email_sent",
        extra={
            "booking_reference": booking.reference,
            "hours_before": hours_before,
        },
    )
    return True
