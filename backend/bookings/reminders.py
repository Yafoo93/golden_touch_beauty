from datetime import timedelta

from django.utils import timezone

from notifications.jobs import enqueue_email_job

from .models import Booking


REMINDER_HOURS = (24, 6)
REMINDER_STATUSES = (Booking.Status.CONFIRMED, Booking.Status.RESCHEDULED)


def schedule_booking_reminders(booking):
    """Create idempotent, future email jobs for a confirmed appointment."""
    if booking.status not in REMINDER_STATUSES or not booking.customer_id:
        return []

    now = timezone.now()
    scheduled_start = booking.preferred_start.isoformat()
    jobs = []
    for hours_before in REMINDER_HOURS:
        send_at = booking.preferred_start - timedelta(hours=hours_before)
        if send_at <= now:
            continue
        jobs.append(
            enqueue_email_job(
                job_type="booking_reminder",
                object_id=booking.pk,
                event=str(hours_before),
                payload={"scheduled_start": scheduled_start},
                unique_key=(
                    f"booking:{booking.pk}:reminder:{hours_before}:"
                    f"{scheduled_start}"
                ),
                next_attempt_at=send_at,
            )
        )
    return jobs


def reconcile_booking_reminders():
    """Backfill reminder jobs for existing future confirmed appointments."""
    bookings = Booking.objects.filter(
        customer__isnull=False,
        preferred_start__gt=timezone.now(),
        status__in=REMINDER_STATUSES,
    ).only("id", "customer_id", "preferred_start", "status")
    return sum(len(schedule_booking_reminders(booking)) for booking in bookings)
