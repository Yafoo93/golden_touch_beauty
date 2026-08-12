import logging
from datetime import timedelta

from django.conf import settings
from django.core.mail import send_mail
from django.db import transaction
from django.utils import timezone

from .models import EmailJob


logger = logging.getLogger("golden_touch.notifications")


def enqueue_email_job(
    *, job_type, unique_key, object_id=None, event="", payload=None,
    next_attempt_at=None,
):
    """Persist an idempotent email job and optionally execute it in test mode."""
    job, created = EmailJob.objects.get_or_create(
        unique_key=unique_key,
        defaults={
            "job_type": job_type,
            "object_id": object_id,
            "event": event,
            "payload": payload or {},
            "next_attempt_at": next_attempt_at or timezone.now(),
        },
    )
    if created and getattr(settings, "EMAIL_JOBS_EAGER", False):
        process_email_job(job.pk)
        job.refresh_from_db()
    return job


def _deliver(job):
    if job.job_type == "raw":
        payload = job.payload
        return bool(
            send_mail(
                subject=payload["subject"],
                message=payload["message"],
                from_email=payload.get("from_email") or settings.DEFAULT_FROM_EMAIL,
                recipient_list=payload["recipient_list"],
                html_message=payload.get("html_message"),
                fail_silently=False,
            )
        )
    if job.job_type.startswith("booking_"):
        from bookings.emails import (
            send_booking_confirmation_email,
            send_booking_reminder_email,
            send_booking_update_email,
        )
        from bookings.models import Booking

        booking = Booking.objects.select_related("customer", "branch").prefetch_related(
            "service_items"
        ).get(pk=job.object_id)
        if job.job_type == "booking_confirmation":
            return send_booking_confirmation_email(booking)
        if job.job_type == "booking_reminder":
            return send_booking_reminder_email(
                booking,
                hours_before=int(job.event),
                scheduled_start=job.payload.get("scheduled_start", ""),
            )
        return send_booking_update_email(booking, job.event)
    if job.job_type.startswith("order_"):
        from orders.emails import send_order_confirmation_email, send_order_status_email
        from orders.models import Order

        order = Order.objects.select_related("customer", "branch").prefetch_related(
            "items"
        ).get(pk=job.object_id)
        if job.job_type == "order_confirmation":
            return send_order_confirmation_email(order)
        return send_order_status_email(order, job.event)
    if job.job_type == "payment_receipt":
        from payments.emails import send_receipt_email
        from payments.models import Receipt

        receipt = Receipt.objects.select_related(
            "customer", "branch", "payment"
        ).get(pk=job.object_id)
        return send_receipt_email(receipt)
    raise ValueError(f"Unsupported email job type: {job.job_type}")


def _claim_job(job_id):
    with transaction.atomic():
        stale_before = timezone.now() - timedelta(minutes=15)
        job = EmailJob.objects.select_for_update().get(pk=job_id)
        if job.status == EmailJob.Status.PROCESSING and job.started_at:
            if job.started_at > stale_before:
                return None
        elif job.status != EmailJob.Status.PENDING:
            return None
        if job.next_attempt_at > timezone.now():
            return None
        job.status = EmailJob.Status.PROCESSING
        job.started_at = timezone.now()
        job.attempts += 1
        job.save(update_fields=["status", "started_at", "attempts", "updated_at"])
        return job


def process_email_job(job_id):
    """Claim and deliver one job, recording success or a bounded retry."""
    job = _claim_job(job_id)
    if job is None:
        return False
    try:
        delivered = _deliver(job)
        if not delivered:
            raise RuntimeError("The email delivery function did not send a message.")
    except Exception as exc:
        logger.exception(
            "background_email_job_failed",
            extra={"email_job_id": str(job.pk), "job_type": job.job_type},
        )
        job.refresh_from_db()
        job.last_error = str(exc)[:4000]
        if job.attempts >= job.max_attempts:
            job.status = EmailJob.Status.FAILED
        else:
            job.status = EmailJob.Status.PENDING
            delay_seconds = min(60 * (2 ** (job.attempts - 1)), 3600)
            job.next_attempt_at = timezone.now() + timedelta(seconds=delay_seconds)
        job.save(
            update_fields=[
                "status", "last_error", "next_attempt_at", "updated_at"
            ]
        )
        return False
    job.refresh_from_db()
    job.status = EmailJob.Status.COMPLETED
    job.completed_at = timezone.now()
    job.last_error = ""
    job.save(
        update_fields=["status", "completed_at", "last_error", "updated_at"]
    )
    return True


def process_due_email_jobs(*, limit=25):
    job_ids = list(
        EmailJob.objects.filter(
            status=EmailJob.Status.PENDING,
            next_attempt_at__lte=timezone.now(),
        )
        .order_by("next_attempt_at", "created_at")
        .values_list("pk", flat=True)[:limit]
    )
    return sum(process_email_job(job_id) for job_id in job_ids)
