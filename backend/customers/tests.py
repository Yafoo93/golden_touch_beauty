from datetime import timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from rest_framework import status

from bookings.models import Booking, BookingServiceItem
from branches.models import Branch
from orders.models import Order
from payments.models import Invoice
from services.models import Service, ServiceCategory
from .models import CustomerAddress, CustomerConsent


User = get_user_model()


class CustomerAccountOverviewTests(TestCase):
    def setUp(self):
        self.customer = User.objects.create_user(
            email="overview@example.com",
            phone_number="+233241000601",
            full_name="Overview Customer",
            password="CustomerPass123!",
        )
        self.other = User.objects.create_user(
            email="other-overview@example.com",
            phone_number="+233241000602",
            full_name="Other Customer",
            password="CustomerPass123!",
        )
        self.branch = Branch.objects.create(
            name="Overview Makola",
            code="OVERVIEW-MAKOLA",
            address="Accra",
            telephone_number="+233241370429",
            opening_days=["monday"],
            opening_time="07:30",
            closing_time="17:00",
        )
        category = ServiceCategory.objects.create(
            name="Overview services", slug="overview-services"
        )
        self.service = Service.objects.create(
            category=category,
            name="Overview Facial",
            slug="overview-facial",
            short_description="Facial",
            description="Facial",
            price="250.00",
            duration_minutes=60,
        )

    def booking(self, customer, status_value, days):
        booking = Booking.objects.create(
            branch=self.branch,
            customer=customer,
            status=status_value,
            preferred_start=timezone.now() + timedelta(days=days),
            total_amount=Decimal("250.00"),
            total_duration_minutes=60,
            recipient_name=customer.full_name,
            recipient_phone=customer.phone_number,
        )
        BookingServiceItem.objects.create(
            booking=booking,
            service=self.service,
            service_name=self.service.name,
            unit_price=Decimal("250.00"),
            duration_minutes=60,
        )
        return booking

    def test_overview_returns_live_customer_totals(self):
        upcoming = self.booking(self.customer, Booking.Status.CONFIRMED, 2)
        self.booking(self.customer, Booking.Status.COMPLETED, -2)
        self.booking(self.other, Booking.Status.CONFIRMED, 3)
        order = Order.objects.create(
            branch=self.branch,
            customer=self.customer,
            total_amount=Decimal("120.00"),
            recipient_name=self.customer.full_name,
            recipient_phone=self.customer.phone_number,
        )
        Invoice.objects.create(
            branch=self.branch,
            customer=self.customer,
            booking=upcoming,
            source_type="booking",
            source_reference=upcoming.reference,
            recipient_name=self.customer.full_name,
            recipient_email=self.customer.email,
            subtotal=Decimal("250.00"),
            total_amount=Decimal("250.00"),
            line_items=[],
        )

        self.client.force_login(self.customer)
        response = self.client.get(reverse("customers:overview"))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            response.json()["summary"],
            {
                "upcoming_appointments": 1,
                "completed_services": 1,
                "orders": 1,
                "outstanding_balance": "250.00",
                "currency": "GHS",
            },
        )
        self.assertEqual(
            response.json()["upcoming_appointments"][0]["reference"],
            upcoming.reference,
        )
        self.assertEqual(
            response.json()["recent_orders"][0]["reference"], order.reference
        )

    def test_overview_never_includes_another_customers_records(self):
        other_booking = self.booking(self.other, Booking.Status.CONFIRMED, 2)
        Order.objects.create(
            branch=self.branch,
            customer=self.other,
            total_amount=Decimal("900.00"),
            recipient_name=self.other.full_name,
            recipient_phone=self.other.phone_number,
        )
        self.client.force_login(self.customer)

        response = self.client.get(reverse("customers:overview"))

        body = response.json()
        self.assertEqual(body["summary"]["upcoming_appointments"], 0)
        self.assertEqual(body["summary"]["orders"], 0)
        self.assertNotIn(other_booking.reference, str(body))

    def test_overview_requires_authentication(self):
        response = self.client.get(reverse("customers:overview"))
        self.assertIn(
            response.status_code,
            (status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN),
        )


class CustomerAddressApiTests(TestCase):
    def setUp(self):
        self.customer = User.objects.create_user(
            email="address@example.com", phone_number="+233241000701",
            full_name="Address Customer", password="CustomerPass123!",
        )
        self.other = User.objects.create_user(
            email="address-other@example.com", phone_number="+233241000702",
            full_name="Other Address Customer", password="CustomerPass123!",
        )
        self.client.force_login(self.customer)

    def payload(self, **overrides):
        data = {
            "label": "Home", "address_type": "both",
            "recipient_name": "Address Customer", "recipient_phone": "024 100 0701",
            "address_line_1": "12 Independence Avenue", "address_line_2": "",
            "city": "Accra", "region": "Greater Accra", "landmark": "Near the clinic",
            "country": "Ghana", "is_default_billing": True, "is_default_delivery": True,
        }
        data.update(overrides)
        return data

    def test_customer_can_create_list_update_and_delete_an_address(self):
        created = self.client.post(reverse("customers:address-list"), self.payload(), content_type="application/json")
        self.assertEqual(created.status_code, status.HTTP_201_CREATED)
        self.assertEqual(created.json()["recipient_phone"], "+233241000701")
        address_id = created.json()["id"]

        listed = self.client.get(reverse("customers:address-list"))
        self.assertEqual(listed.json()["count"], 1)
        self.assertEqual(listed.json()["results"][0]["label"], "Home")

        updated = self.client.patch(
            reverse("customers:address-detail", args=[address_id]),
            {"label": "Main home"}, content_type="application/json",
        )
        self.assertEqual(updated.status_code, status.HTTP_200_OK)
        self.assertEqual(updated.json()["label"], "Main home")
        deleted = self.client.delete(reverse("customers:address-detail", args=[address_id]))
        self.assertEqual(deleted.status_code, status.HTTP_204_NO_CONTENT)

    def test_new_default_replaces_the_previous_default(self):
        first = self.client.post(reverse("customers:address-list"), self.payload(), content_type="application/json")
        second = self.client.post(
            reverse("customers:address-list"),
            self.payload(label="Office", address_line_1="44 Business Road"),
            content_type="application/json",
        )
        self.assertEqual(second.status_code, status.HTTP_201_CREATED)
        old = CustomerAddress.objects.get(pk=first.json()["id"])
        self.assertFalse(old.is_default_billing)
        self.assertFalse(old.is_default_delivery)

    def test_customer_cannot_access_another_customers_address(self):
        address = CustomerAddress.objects.create(
            customer=self.other, label="Private", address_type="delivery",
            recipient_name=self.other.full_name, recipient_phone=self.other.phone_number,
            address_line_1="Private road", city="Accra", region="Greater Accra",
        )
        response = self.client.get(reverse("customers:address-detail", args=[address.pk]))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_address_type_must_support_selected_default(self):
        response = self.client.post(
            reverse("customers:address-list"),
            self.payload(address_type="delivery", is_default_billing=True),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class CustomerConsentApiTests(TestCase):
    def setUp(self):
        self.customer = User.objects.create_user(
            email="consent@example.com", phone_number="+233241000801",
            full_name="Consent Customer", password="CustomerPass123!",
        )
        self.client.force_login(self.customer)

    def test_customer_can_read_and_update_independent_consent_settings(self):
        initial = self.client.get(reverse("customers:consent"))
        self.assertEqual(initial.status_code, status.HTTP_200_OK)
        self.assertFalse(initial.json()["marketing_consent"])
        self.assertFalse(initial.json()["photograph_consent"])

        updated = self.client.patch(
            reverse("customers:consent"),
            {"marketing_consent": True, "photograph_consent": True},
            content_type="application/json",
        )
        self.assertEqual(updated.status_code, status.HTTP_200_OK)
        self.assertTrue(updated.json()["marketing_consent"])
        self.assertTrue(updated.json()["photograph_consent"])
        self.assertIsNotNone(updated.json()["marketing_consent_updated_at"])
        self.assertIsNotNone(updated.json()["photograph_consent_updated_at"])

    def test_customer_can_withdraw_consent(self):
        now = timezone.now()
        CustomerConsent.objects.create(
            user=self.customer, terms_version="test", privacy_version="test",
            terms_privacy_accepted_at=now, marketing_consent=True,
            marketing_consent_updated_at=now, photograph_consent=True,
            photograph_consent_updated_at=now,
        )
        response = self.client.patch(
            reverse("customers:consent"),
            {"marketing_consent": False, "photograph_consent": False},
            content_type="application/json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(response.json()["marketing_consent"])
        self.assertFalse(response.json()["photograph_consent"])

    def test_consent_requires_authentication(self):
        self.client.logout()
        response = self.client.get(reverse("customers:consent"))
        self.assertIn(response.status_code, (status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN))
