import uuid
from datetime import datetime, timedelta
from unittest.mock import patch

from django.core import mail
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from rest_framework import status

from branches.models import Branch, BranchStaffAssignment
from payments.models import Invoice
from notifications.jobs import process_email_job
from notifications.models import EmailJob, Notification
from services.models import Service, ServiceBranchAvailability, ServiceCategory

from .models import Booking, BookingBlock, BookingHistory


User = get_user_model()


class BookingWorkflowApiTests(TestCase):
    def setUp(self):
        self.customer = User.objects.create_user(
            email="booking@example.com",
            phone_number="+233241000201",
            full_name="Booking Customer",
            password="CustomerPass123!",
        )
        self.owner = User.objects.create_superuser(
            email="booking-owner@example.com",
            phone_number="+233241000202",
            full_name="Booking Owner",
            password="OwnerPass123!",
        )
        self.branch = Branch.objects.create(
            name="Booking Makola",
            code="BOOKING-MAKOLA",
            address="Accra",
            telephone_number="+233241370429",
            opening_days=[
                "monday", "tuesday", "wednesday", "thursday", "friday",
                "saturday", "sunday",
            ],
            opening_time="07:30",
            closing_time="19:00",
        )
        category = ServiceCategory.objects.create(
            name="Booking services", slug="booking-services"
        )
        self.facial = Service.objects.create(
            category=category,
            name="Booking Facial",
            slug="booking-facial",
            short_description="Facial",
            description="Facial",
            price="200.00",
            price_type=Service.PriceType.FIXED,
            duration_minutes=60,
            is_active=True,
            is_published=True,
            allows_pay_at_clinic=True,
        )
        self.hair = Service.objects.create(
            category=category,
            name="Booking Hair",
            slug="booking-hair",
            short_description="Hair",
            description="Hair",
            price="150.00",
            price_type=Service.PriceType.FIXED,
            duration_minutes=90,
            is_active=True,
            is_published=True,
            allows_pay_at_clinic=True,
        )
        ServiceBranchAvailability.objects.create(
            branch=self.branch, service=self.facial
        )
        ServiceBranchAvailability.objects.create(
            branch=self.branch, service=self.hair
        )
        selected_date = timezone.localdate() + timedelta(days=3)
        self.preferred_start = timezone.make_aware(
            datetime.combine(
                selected_date,
                datetime.strptime("10:00", "%H:%M").time(),
            ),
            timezone.get_current_timezone(),
        )

    def payload(self, **overrides):
        payload = {
            "client_request_id": str(uuid.uuid4()),
            "branch_code": self.branch.code,
            "preferred_start": self.preferred_start.isoformat(),
            "service_selections": [
                {"service_id": str(self.facial.id)},
                {"service_id": str(self.hair.id)},
            ],
            "recipient_is_customer": True,
            "recipient_name": self.customer.full_name,
            "recipient_phone": self.customer.phone_number,
            "allergies": "None known",
            "conditions": "",
            "previous_treatments": "",
            "notes": "Please call on arrival.",
            "photo_marketing_consent": False,
            "payment_method": "clinic",
        }
        payload.update(overrides)
        return payload

    def test_customer_can_create_multi_service_booking_once(self):
        self.client.force_login(self.customer)
        payload = self.payload()

        first = self.client.post(
            reverse("bookings:customer-list"),
            payload,
            content_type="application/json",
        )
        repeated = self.client.post(
            reverse("bookings:customer-list"),
            payload,
            content_type="application/json",
        )

        self.assertEqual(first.status_code, status.HTTP_201_CREATED)
        self.assertEqual(repeated.status_code, status.HTTP_200_OK)
        self.assertEqual(first.json()["reference"], repeated.json()["reference"])
        self.assertEqual(first.json()["total_amount"], "350.00")
        self.assertEqual(first.json()["total_duration_minutes"], 150)
        self.assertEqual(len(first.json()["services"]), 2)
        self.assertEqual(Booking.objects.count(), 1)
        invoice = Invoice.objects.get()
        self.assertEqual(invoice.source_reference, first.json()["reference"])
        self.assertEqual(invoice.branch, self.branch)
        self.assertEqual(invoice.customer, self.customer)
        self.assertEqual(invoice.total_amount, 350)
        self.assertEqual(len(invoice.line_items), 2)
        self.assertEqual(BookingHistory.objects.get().action, "created")
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, [self.customer.email])
        self.assertIn(first.json()["reference"], mail.outbox[0].body)
        self.assertIn(
            f"/book/confirmation/{first.json()['reference']}",
            mail.outbox[0].body,
        )
        self.assertIn("Booking Facial", mail.outbox[0].body)
        self.assertNotIn("None known", mail.outbox[0].body)

        dashboard = self.client.get(reverse("bookings:customer-list"))
        self.assertEqual(dashboard.status_code, status.HTTP_200_OK)
        self.assertEqual(dashboard.json()["count"], 1)
        self.assertEqual(
            dashboard.json()["results"][0]["reference"],
            first.json()["reference"],
        )

    def test_booking_requires_authentication(self):
        response = self.client.post(
            reverse("bookings:customer-list"),
            self.payload(),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    @patch(
        "bookings.emails.send_mail",
        side_effect=RuntimeError("Temporary email provider failure"),
    )
    def test_email_failure_does_not_undo_booking(self, _send_mail):
        self.client.force_login(self.customer)

        with self.assertLogs("golden_touch.notifications", level="ERROR"):
            response = self.client.post(
                reverse("bookings:customer-list"),
                self.payload(
                    service_selections=[{"service_id": str(self.facial.id)}]
                ),
                content_type="application/json",
            )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(
            Booking.objects.filter(reference=response.json()["reference"]).exists()
        )

    def test_duplicate_active_service_booking_is_rejected(self):
        self.client.force_login(self.customer)
        first = self.client.post(
            reverse("bookings:customer-list"),
            self.payload(service_selections=[{"service_id": str(self.facial.id)}]),
            content_type="application/json",
        )
        second = self.client.post(
            reverse("bookings:customer-list"),
            self.payload(service_selections=[{"service_id": str(self.facial.id)}]),
            content_type="application/json",
        )
        self.assertEqual(first.status_code, status.HTTP_201_CREATED)
        self.assertEqual(second.status_code, status.HTTP_400_BAD_REQUEST)

    def test_past_confirmed_booking_does_not_block_a_new_request(self):
        self.client.force_login(self.customer)
        first = self.client.post(
            reverse("bookings:customer-list"),
            self.payload(service_selections=[{"service_id": str(self.facial.id)}]),
            content_type="application/json",
        )
        self.assertEqual(first.status_code, status.HTTP_201_CREATED)
        Booking.objects.filter(reference=first.json()["reference"]).update(
            status=Booking.Status.CONFIRMED,
            preferred_start=timezone.now() - timedelta(days=1),
        )

        second = self.client.post(
            reverse("bookings:customer-list"),
            self.payload(service_selections=[{"service_id": str(self.facial.id)}]),
            content_type="application/json",
        )

        self.assertEqual(second.status_code, status.HTTP_201_CREATED)

    def test_pay_at_clinic_must_be_allowed_by_every_service(self):
        self.hair.allows_pay_at_clinic = False
        self.hair.save(update_fields=["allows_pay_at_clinic", "updated_at"])
        self.client.force_login(self.customer)
        response = self.client.post(
            reverse("bookings:customer-list"),
            self.payload(),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("payment_method", response.json()["error"]["details"])

    def test_blocked_period_is_excluded_from_availability(self):
        selected_date = (timezone.localdate() + timedelta(days=2))
        tz = timezone.get_current_timezone()
        blocked_start = timezone.make_aware(
            datetime.combine(selected_date, datetime.strptime("09:00", "%H:%M").time()),
            tz,
        )
        BookingBlock.objects.create(
            branch=self.branch,
            starts_at=blocked_start,
            ends_at=blocked_start + timedelta(hours=1),
            block_type=BookingBlock.BlockType.MEETING,
            reason="Team meeting",
        )
        response = self.client.get(
            reverse("bookings:availability"),
            {
                "branch": self.branch.code,
                "date": selected_date.isoformat(),
                "duration": 60,
            },
        )
        values = [slot["value"] for slot in response.json()["slots"]]
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(any(value.startswith(blocked_start.isoformat()[:16]) for value in values))

    def test_management_can_propose_and_customer_can_accept_time(self):
        self.client.force_login(self.customer)
        created = self.client.post(
            reverse("bookings:customer-list"),
            self.payload(service_selections=[{"service_id": str(self.facial.id)}]),
            content_type="application/json",
        ).json()
        proposed = self.preferred_start + timedelta(days=1)
        self.client.force_login(self.owner)
        with self.captureOnCommitCallbacks(execute=True):
            action = self.client.post(
                reverse("bookings:management-action", args=[created["reference"]]),
                {"action": "propose_time", "proposed_start": proposed.isoformat()},
                content_type="application/json",
            )
        self.assertEqual(action.status_code, status.HTTP_200_OK)
        self.assertEqual(action.json()["status"], "proposed")
        self.assertEqual(len(mail.outbox), 2)
        self.assertIn("New appointment time proposed", mail.outbox[-1].subject)
        self.assertIn(proposed.strftime("%d %B %Y"), mail.outbox[-1].body)
        self.assertNotIn("None known", mail.outbox[-1].body)

        self.client.force_login(self.customer)
        with self.captureOnCommitCallbacks(execute=True):
            accepted = self.client.post(
                reverse("bookings:customer-proposal", args=[created["reference"]]),
                {"accepted": True},
                content_type="application/json",
            )
        self.assertEqual(accepted.status_code, status.HTTP_200_OK)
        self.assertEqual(accepted.json()["status"], "confirmed")
        self.assertEqual(len(mail.outbox), 3)
        self.assertIn("New appointment time confirmed", mail.outbox[-1].subject)
        self.assertEqual(
            Booking.objects.get(reference=created["reference"]).preferred_start,
            proposed,
        )

    def test_management_cancellation_sends_customer_message(self):
        self.client.force_login(self.customer)
        created = self.client.post(
            reverse("bookings:customer-list"),
            self.payload(service_selections=[{"service_id": str(self.facial.id)}]),
            content_type="application/json",
        ).json()

        self.client.force_login(self.owner)
        with self.captureOnCommitCallbacks(execute=True):
            response = self.client.post(
                reverse("bookings:management-action", args=[created["reference"]]),
                {"action": "cancel", "reason": "Internal scheduling note"},
                content_type="application/json",
            )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()["status"], "cancelled")
        self.assertEqual(len(mail.outbox), 2)
        self.assertIn("Appointment cancelled", mail.outbox[-1].subject)
        self.assertNotIn("Internal scheduling note", mail.outbox[-1].body)

    def test_confirmation_schedules_24_and_6_hour_reminders(self):
        self.client.force_login(self.customer)
        created = self.client.post(
            reverse("bookings:customer-list"),
            self.payload(service_selections=[{"service_id": str(self.facial.id)}]),
            content_type="application/json",
        ).json()

        self.client.force_login(self.owner)
        with self.captureOnCommitCallbacks(execute=True):
            response = self.client.post(
                reverse("bookings:management-action", args=[created["reference"]]),
                {"action": "confirm"},
                content_type="application/json",
            )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        booking = Booking.objects.get(reference=created["reference"])
        reminders = EmailJob.objects.filter(
            job_type="booking_reminder", object_id=booking.pk
        ).order_by("event")
        self.assertEqual(list(reminders.values_list("event", flat=True)), ["24", "6"])
        for reminder in reminders:
            expected = booking.preferred_start - timedelta(hours=int(reminder.event))
            self.assertEqual(reminder.next_attempt_at, expected)

        reminder = reminders.get(event="24")
        reminder.next_attempt_at = timezone.now()
        reminder.save(update_fields=["next_attempt_at", "updated_at"])
        self.assertTrue(process_email_job(reminder.pk))
        self.assertIn("24 hours to go", mail.outbox[-1].subject)
        self.assertTrue(
            Notification.objects.filter(
                recipient=self.customer,
                event_key__contains=":reminder:24:",
            ).exists()
        )

    def test_cancelled_booking_reminder_is_safely_skipped(self):
        self.client.force_login(self.customer)
        created = self.client.post(
            reverse("bookings:customer-list"),
            self.payload(service_selections=[{"service_id": str(self.facial.id)}]),
            content_type="application/json",
        ).json()
        booking = Booking.objects.get(reference=created["reference"])
        booking.status = Booking.Status.CONFIRMED
        booking.save(update_fields=["status", "updated_at"])
        from .reminders import schedule_booking_reminders

        reminder = schedule_booking_reminders(booking)[0]
        booking.status = Booking.Status.CANCELLED
        booking.save(update_fields=["status", "updated_at"])
        reminder.next_attempt_at = timezone.now()
        reminder.save(update_fields=["next_attempt_at", "updated_at"])
        email_count = len(mail.outbox)

        self.assertTrue(process_email_job(reminder.pk))
        self.assertEqual(len(mail.outbox), email_count)
        self.assertFalse(
            Notification.objects.filter(event_key__contains=":reminder:").exists()
        )

    @patch(
        "bookings.emails.send_mail",
        side_effect=RuntimeError("Temporary email provider failure"),
    )
    def test_change_email_failure_does_not_undo_confirmation(self, _send_mail):
        self.client.force_login(self.customer)
        created = self.client.post(
            reverse("bookings:customer-list"),
            self.payload(service_selections=[{"service_id": str(self.facial.id)}]),
            content_type="application/json",
        ).json()

        self.client.force_login(self.owner)
        with self.assertLogs("golden_touch.notifications", level="ERROR"):
            with self.captureOnCommitCallbacks(execute=True):
                response = self.client.post(
                    reverse(
                        "bookings:management-action",
                        args=[created["reference"]],
                    ),
                    {"action": "confirm"},
                    content_type="application/json",
                )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            Booking.objects.get(reference=created["reference"]).status,
            Booking.Status.CONFIRMED,
        )

    def test_owner_management_list_contains_customer_pending_booking(self):
        self.client.force_login(self.customer)
        created = self.client.post(
            reverse("bookings:customer-list"),
            self.payload(service_selections=[{"service_id": str(self.facial.id)}]),
            content_type="application/json",
        )
        self.assertEqual(created.status_code, status.HTTP_201_CREATED)

        self.client.force_login(self.owner)
        response = self.client.get(reverse("bookings:management-list"))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()["count"], 1)
        self.assertEqual(
            response.json()["results"][0]["reference"],
            created.json()["reference"],
        )
        self.assertEqual(response.json()["results"][0]["status"], "pending")

    def test_receptionist_cannot_receive_sensitive_booking_intake(self):
        receptionist = User.objects.create_user(
            email="booking-reception@example.com", phone_number="+233241000299",
            full_name="Booking Receptionist", password="ReceptionPass123!", is_staff=True,
        )
        BranchStaffAssignment.objects.create(
            branch=self.branch, staff=receptionist,
            roles=[BranchStaffAssignment.Role.RECEPTIONIST], assigned_by=self.owner,
        )
        self.client.force_login(self.customer)
        created = self.client.post(
            reverse("bookings:customer-list"), self.payload(allergies="Private allergy", conditions="Private condition"),
            content_type="application/json",
        ).json()

        self.client.force_login(receptionist)
        response = self.client.get(reverse("bookings:management-detail", args=[created["reference"]]))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(response.json()["can_view_sensitive_intake"])
        for field in ("allergies", "conditions", "previous_treatments", "notes"):
            self.assertNotIn(field, response.json())

    def test_stock_manager_cannot_access_booking_operations(self):
        stock_manager = User.objects.create_user(
            email="booking-stock@example.com", phone_number="+233241000298",
            full_name="Booking Stock Manager", password="StockPass123!", is_staff=True,
        )
        BranchStaffAssignment.objects.create(
            branch=self.branch, staff=stock_manager,
            roles=[BranchStaffAssignment.Role.STOCK_MANAGER], assigned_by=self.owner,
        )
        self.client.force_login(stock_manager)
        response = self.client.get(reverse("bookings:management-list"))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_customer_can_filter_appointments_by_status(self):
        self.client.force_login(self.customer)
        first = self.client.post(
            reverse("bookings:customer-list"),
            self.payload(service_selections=[{"service_id": str(self.facial.id)}]),
            content_type="application/json",
        )
        self.assertEqual(first.status_code, status.HTTP_201_CREATED)
        confirmed = Booking.objects.get(reference=first.json()["reference"])
        confirmed.status = Booking.Status.CONFIRMED
        confirmed.save(update_fields=["status", "updated_at"])
        Booking.objects.create(
            branch=self.branch,
            customer=self.customer,
            status=Booking.Status.CANCELLED,
            preferred_start=self.preferred_start + timedelta(days=2),
            recipient_name=self.customer.full_name,
            recipient_phone=self.customer.phone_number,
        )

        response = self.client.get(
            reverse("bookings:customer-list"), {"status": "confirmed"}
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()["count"], 1)
        self.assertEqual(
            response.json()["results"][0]["reference"], confirmed.reference
        )

    def test_customer_booking_filter_rejects_unknown_status(self):
        self.client.force_login(self.customer)
        response = self.client.get(
            reverse("bookings:customer-list"), {"status": "unknown"}
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_customer_cannot_view_another_customers_booking(self):
        self.client.force_login(self.customer)
        created = self.client.post(
            reverse("bookings:customer-list"),
            self.payload(service_selections=[{"service_id": str(self.facial.id)}]),
            content_type="application/json",
        ).json()
        other = User.objects.create_user(
            email="booking-other@example.com",
            phone_number="+233241000203",
            full_name="Other Booking Customer",
            password="CustomerPass123!",
        )
        self.client.force_login(other)
        response = self.client.get(
            reverse("bookings:customer-detail", args=[created["reference"]])
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_customer_history_excludes_internal_management_details(self):
        booking = Booking.objects.create(
            branch=self.branch,
            customer=self.customer,
            status=Booking.Status.CANCELLED,
            preferred_start=self.preferred_start,
            recipient_name=self.customer.full_name,
            recipient_phone=self.customer.phone_number,
        )
        BookingHistory.objects.create(
            booking=booking,
            action="cancel",
            from_status=Booking.Status.CONFIRMED,
            to_status=Booking.Status.CANCELLED,
            reason="Internal staffing shortage and private note",
            actor=self.owner,
            metadata={"internal": "do not expose"},
        )
        self.client.force_login(self.customer)

        response = self.client.get(
            reverse("bookings:customer-detail", args=[booking.reference])
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        history = response.json()["history"][0]
        self.assertNotIn("reason", history)
        self.assertNotIn("metadata", history)
        self.assertNotIn("actor_name", history)
        self.assertNotIn("private note", str(response.json()))
