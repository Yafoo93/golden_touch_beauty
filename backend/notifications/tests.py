from django.contrib.auth import get_user_model
from django.core import mail
from django.core.management import call_command
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from unittest.mock import patch

from .jobs import enqueue_email_job, process_email_job
from .models import EmailJob, Notification
from .services import create_notification


User = get_user_model()


class NotificationApiTests(TestCase):
    def setUp(self):
        self.customer = User.objects.create_user(
            email="notifications@example.com",
            phone_number="+233241000501",
            full_name="Notification Customer",
            password="CustomerPass123!",
        )
        self.other = User.objects.create_user(
            email="other-notifications@example.com",
            phone_number="+233241000502",
            full_name="Other Customer",
            password="CustomerPass123!",
        )
        self.notification = create_notification(
            recipient=self.customer,
            category=Notification.Category.ORDER,
            title="Order ready",
            message="Your order is ready for pickup.",
            action_url="/account",
            event_key="test:order:ready",
        )

    def test_list_requires_authentication(self):
        response = self.client.get(reverse("notifications:list"))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_list_contains_only_current_customers_notifications(self):
        create_notification(
            recipient=self.other,
            category=Notification.Category.BOOKING,
            title="Other booking",
            message="This belongs to another customer.",
            action_url="/account",
            event_key="test:other:booking",
        )
        self.client.force_login(self.customer)

        response = self.client.get(reverse("notifications:list"))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()["unread_count"], 1)
        self.assertEqual(len(response.json()["notifications"]), 1)
        self.assertEqual(
            response.json()["notifications"][0]["title"], "Order ready"
        )

    def test_customer_can_mark_own_notification_read(self):
        self.client.force_login(self.customer)
        response = self.client.post(
            reverse("notifications:read", args=[self.notification.pk]),
            {},
            content_type="application/json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.notification.refresh_from_db()
        self.assertIsNotNone(self.notification.read_at)
        self.assertTrue(response.json()["is_read"])

    def test_customer_cannot_mark_another_customers_notification_read(self):
        self.client.force_login(self.other)
        response = self.client.post(
            reverse("notifications:read", args=[self.notification.pk]),
            {},
            content_type="application/json",
        )

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.notification.refresh_from_db()
        self.assertIsNone(self.notification.read_at)

    def test_mark_all_only_changes_current_customers_notifications(self):
        other_notification = create_notification(
            recipient=self.other,
            category=Notification.Category.SYSTEM,
            title="Other alert",
            message="Other message.",
            action_url="/account",
            event_key="test:other:alert",
        )
        self.client.force_login(self.customer)

        response = self.client.post(
            reverse("notifications:read-all"),
            {},
            content_type="application/json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json(), {"updated": 1, "unread_count": 0})
        self.notification.refresh_from_db()
        other_notification.refresh_from_db()
        self.assertIsNotNone(self.notification.read_at)
        self.assertIsNone(other_notification.read_at)

    def test_event_key_makes_notification_creation_idempotent(self):
        repeated = create_notification(
            recipient=self.customer,
            category=Notification.Category.ORDER,
            title="Changed title",
            message="Changed message.",
            action_url="/changed",
            event_key="test:order:ready",
        )

        self.assertEqual(repeated.pk, self.notification.pk)
        self.assertEqual(Notification.objects.count(), 1)
        self.assertEqual(repeated.title, "Order ready")

    def test_list_supports_category_read_state_and_pagination(self):
        self.notification.mark_read()
        create_notification(
            recipient=self.customer,
            category=Notification.Category.BOOKING,
            title="Booking confirmed",
            message="Your appointment is confirmed.",
            action_url="/account",
            event_key="test:booking:confirmed",
        )
        self.client.force_login(self.customer)

        response = self.client.get(
            reverse("notifications:list"),
            {"category": "booking", "read": "unread", "limit": 1},
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()["total"], 1)
        self.assertEqual(response.json()["unread_count"], 1)
        self.assertFalse(response.json()["has_more"])
        self.assertEqual(
            response.json()["notifications"][0]["category"], "booking"
        )


@override_settings(EMAIL_JOBS_EAGER=False)
class EmailJobTests(TestCase):
    def payload(self):
        return {
            "subject": "Background test",
            "message": "This message must be delivered by the worker.",
            "recipient_list": ["customer@example.com"],
        }

    def test_email_is_queued_then_delivered_by_worker_command(self):
        job = enqueue_email_job(
            job_type="raw",
            unique_key="test:background:delivery",
            payload=self.payload(),
        )

        self.assertEqual(mail.outbox, [])
        self.assertEqual(job.status, EmailJob.Status.PENDING)

        call_command("process_email_jobs", once=True)

        job.refresh_from_db()
        self.assertEqual(job.status, EmailJob.Status.COMPLETED)
        self.assertEqual(job.attempts, 1)
        self.assertEqual(len(mail.outbox), 1)

    def test_unique_key_prevents_duplicate_email_jobs(self):
        first = enqueue_email_job(
            job_type="raw", unique_key="test:unique", payload=self.payload()
        )
        repeated = enqueue_email_job(
            job_type="raw", unique_key="test:unique", payload=self.payload()
        )

        self.assertEqual(first.pk, repeated.pk)
        self.assertEqual(EmailJob.objects.count(), 1)

    @patch("notifications.jobs.send_mail", side_effect=RuntimeError("SMTP down"))
    def test_failed_delivery_is_scheduled_for_retry(self, _send_mail):
        job = enqueue_email_job(
            job_type="raw",
            unique_key="test:retry",
            payload=self.payload(),
        )

        self.assertFalse(process_email_job(job.pk))

        job.refresh_from_db()
        self.assertEqual(job.status, EmailJob.Status.PENDING)
        self.assertEqual(job.attempts, 1)
        self.assertGreater(job.next_attempt_at, timezone.now())
        self.assertIn("SMTP down", job.last_error)
