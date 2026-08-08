import uuid
from datetime import timedelta
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core import mail
from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from rest_framework import status

from branches.models import Branch
from inventory.models import BranchInventory, StockMovement
from products.models import CustomerCartItem, Product, ProductCategory, ProductVariant

from .models import Order, StockReservation
from .services import capture_order_stock, transition_order_status


User = get_user_model()


class CheckoutApiTests(TestCase):
    def setUp(self):
        self.customer = User.objects.create_user(
            email="checkout@example.com",
            phone_number="+233241000301",
            full_name="Checkout Customer",
            password="CustomerPass123!",
        )
        self.other = User.objects.create_user(
            email="checkout-other@example.com",
            phone_number="+233241000302",
            full_name="Other Customer",
            password="CustomerPass123!",
        )
        self.makola = Branch.objects.create(
            name="Checkout Makola",
            code="CHECKOUT-MAKOLA",
            address="Accra",
            telephone_number="+233241370429",
            opening_days=["monday"],
            opening_time="07:30",
            closing_time="17:00",
        )
        self.tse_addo = Branch.objects.create(
            name="Checkout Tse Addo",
            code="CHECKOUT-TSE-ADDO",
            address="Accra",
            telephone_number="+233207911043",
            opening_days=["monday"],
            opening_time="07:30",
            closing_time="19:00",
        )
        category = ProductCategory.objects.create(
            name="Checkout products", slug="checkout-products"
        )
        product = Product.objects.create(
            category=category,
            name="Checkout Face Cream",
            slug="checkout-face-cream",
            description="Test cream",
            is_active=True,
            is_published=True,
        )
        self.variant = ProductVariant.objects.create(
            product=product,
            name="Standard",
            sku="CHECKOUT-CREAM",
            selling_price="45.00",
            cost_price="20.00",
            is_active=True,
        )
        self.makola_stock = BranchInventory.objects.create(
            branch=self.makola,
            product_variant=self.variant,
            quantity_on_hand=2,
            quantity_reserved=0,
        )
        self.tse_stock = BranchInventory.objects.create(
            branch=self.tse_addo,
            product_variant=self.variant,
            quantity_on_hand=0,
            quantity_reserved=0,
        )

    def add_cart(self, user=None, quantity=1):
        return CustomerCartItem.objects.create(
            customer=user or self.customer,
            variant=self.variant,
            quantity=quantity,
        )

    def payload(self, **overrides):
        payload = {
            "client_request_id": str(uuid.uuid4()),
            "fulfillment_method": "pickup",
            "pickup_branch_code": self.makola.code,
            "recipient_name": self.customer.full_name,
            "recipient_phone": self.customer.phone_number,
            "delivery_address": "",
            "delivery_city": "",
            "delivery_notes": "",
        }
        payload.update(overrides)
        return payload

    def create_order(self, payload=None):
        self.client.force_login(self.customer)
        return self.client.post(
            reverse("orders:checkout-create"),
            payload or self.payload(),
            content_type="application/json",
        )

    def test_checkout_requires_authentication(self):
        response = self.client.get(reverse("orders:checkout-options"))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_options_show_only_branches_with_enough_stock(self):
        self.add_cart(quantity=2)
        self.client.force_login(self.customer)
        response = self.client.get(reverse("orders:checkout-options"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            [branch["code"] for branch in response.json()["pickup_branches"]],
            [self.makola.code],
        )

    def test_checkout_snapshots_cart_and_reserves_for_thirty_minutes(self):
        self.add_cart(quantity=2)
        before = timezone.now()
        response = self.create_order()
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        body = response.json()
        self.assertEqual(body["status"], Order.Status.AWAITING_PAYMENT)
        self.assertEqual(body["subtotal"], "90.00")
        self.assertEqual(body["items"][0]["product_name"], "Checkout Face Cream")
        self.assertEqual(body["items"][0]["unit_price"], "45.00")
        self.assertFalse(CustomerCartItem.objects.filter(customer=self.customer).exists())
        reservation = StockReservation.objects.get(order__reference=body["reference"])
        self.assertGreaterEqual(reservation.expires_at, before + timedelta(minutes=29))
        self.makola_stock.refresh_from_db()
        self.assertEqual(self.makola_stock.quantity_on_hand, 2)
        self.assertEqual(self.makola_stock.quantity_reserved, 2)

    def test_repeating_client_request_creates_exactly_one_order(self):
        self.add_cart()
        payload = self.payload()
        with self.captureOnCommitCallbacks(execute=True):
            first = self.create_order(payload)
            repeated = self.create_order(payload)
        self.assertEqual(first.status_code, status.HTTP_201_CREATED)
        self.assertEqual(repeated.status_code, status.HTTP_200_OK)
        self.assertEqual(first.json()["reference"], repeated.json()["reference"])
        self.assertEqual(Order.objects.count(), 1)
        self.assertEqual(len(mail.outbox), 1)

    def test_new_order_email_contains_confirmation_not_payment_receipt(self):
        self.add_cart(quantity=2)
        with self.captureOnCommitCallbacks(execute=True):
            response = self.create_order()

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(len(mail.outbox), 1)
        email = mail.outbox[0]
        reference = response.json()["reference"]
        self.assertEqual(email.to, [self.customer.email])
        self.assertIn(reference, email.subject)
        self.assertIn("Checkout Face Cream (Standard) x 2", email.body)
        self.assertIn("GHS 90.00", email.body)
        self.assertIn(
            f"/checkout/success?order={reference}",
            email.body,
        )
        self.assertIn("not a payment receipt", email.body)

    @patch("orders.emails.send_mail", side_effect=RuntimeError("SMTP unavailable"))
    def test_email_failure_does_not_undo_order(self, _send_mail):
        self.add_cart()
        with self.captureOnCommitCallbacks(execute=True):
            response = self.create_order()

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(
            Order.objects.filter(reference=response.json()["reference"]).exists()
        )

    def test_delivery_selects_a_fulfillment_branch_internally(self):
        self.add_cart()
        response = self.create_order(
            self.payload(
                fulfillment_method="delivery",
                pickup_branch_code="",
                delivery_address="12 Example Street",
                delivery_city="Accra",
            )
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.json()["branch_code"], self.makola.code)

    def test_sequential_customers_cannot_reserve_the_last_unit_twice(self):
        self.makola_stock.quantity_on_hand = 1
        self.makola_stock.save(update_fields=["quantity_on_hand", "updated_at"])
        self.add_cart(self.customer)
        first = self.create_order()
        self.assertEqual(first.status_code, status.HTTP_201_CREATED)
        self.add_cart(self.other)
        self.client.force_login(self.other)
        second = self.client.post(
            reverse("orders:checkout-create"),
            self.payload(
                recipient_name=self.other.full_name,
                recipient_phone=self.other.phone_number,
            ),
            content_type="application/json",
        )
        self.assertEqual(second.status_code, status.HTTP_409_CONFLICT)
        self.assertEqual(Order.objects.count(), 1)

    def test_cancellation_releases_stock_and_restores_cart(self):
        self.add_cart()
        created = self.create_order().json()
        with self.captureOnCommitCallbacks(execute=True):
            response = self.client.post(
                reverse("orders:customer-cancel", args=[created["reference"]]),
                {},
                content_type="application/json",
            )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()["status"], Order.Status.CANCELLED)
        self.makola_stock.refresh_from_db()
        self.assertEqual(self.makola_stock.quantity_reserved, 0)
        self.assertTrue(CustomerCartItem.objects.filter(customer=self.customer).exists())
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn("Order cancelled", mail.outbox[0].subject)
        self.assertNotIn("12 Example Street", mail.outbox[0].body)

    def test_expiry_command_releases_reservation(self):
        self.add_cart()
        created = self.create_order().json()
        StockReservation.objects.filter(order__reference=created["reference"]).update(
            expires_at=timezone.now() - timedelta(seconds=1)
        )
        call_command("release_expired_order_reservations")
        self.makola_stock.refresh_from_db()
        order = Order.objects.get(reference=created["reference"])
        self.assertEqual(self.makola_stock.quantity_reserved, 0)
        self.assertEqual(order.status, Order.Status.CANCELLED)
        self.assertEqual(order.payment_status, "expired")

    def test_verified_payment_converts_reservation_to_sale_once(self):
        self.add_cart()
        created = self.create_order().json()
        with self.captureOnCommitCallbacks(execute=True):
            order = capture_order_stock(Order.objects.get(reference=created["reference"]))
            repeated = capture_order_stock(order)
        self.assertEqual(repeated.status, Order.Status.PAID)
        self.makola_stock.refresh_from_db()
        self.assertEqual(self.makola_stock.quantity_on_hand, 1)
        self.assertEqual(self.makola_stock.quantity_reserved, 0)
        self.assertEqual(
            StockMovement.objects.filter(
                reference_id=order.reference,
                movement_type=StockMovement.MovementType.SALE,
            ).count(),
            1,
        )
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn("Payment confirmed", mail.outbox[0].subject)

    def test_operational_status_transitions_send_one_message_each(self):
        self.add_cart()
        created = self.create_order().json()
        with self.captureOnCommitCallbacks(execute=True):
            order = capture_order_stock(
                Order.objects.get(reference=created["reference"])
            )
        mail.outbox.clear()

        with self.captureOnCommitCallbacks(execute=True):
            order = transition_order_status(order, Order.Status.PROCESSING)
            repeated = transition_order_status(order, Order.Status.PROCESSING)
            order = transition_order_status(
                repeated, Order.Status.READY_FOR_PICKUP
            )

        self.assertEqual(order.status, Order.Status.READY_FOR_PICKUP)
        self.assertEqual(len(mail.outbox), 2)
        self.assertIn("Order in progress", mail.outbox[0].subject)
        self.assertIn("Order ready for pickup", mail.outbox[1].subject)

    def test_invalid_or_wrong_fulfillment_transition_is_rejected(self):
        self.add_cart()
        created = self.create_order().json()
        with self.captureOnCommitCallbacks(execute=True):
            order = capture_order_stock(
                Order.objects.get(reference=created["reference"])
            )
            order = transition_order_status(order, Order.Status.PROCESSING)

        with self.assertRaisesMessage(ValueError, "Only delivery orders"):
            transition_order_status(order, Order.Status.SHIPPED)

    @patch("orders.emails.send_mail", side_effect=RuntimeError("SMTP unavailable"))
    def test_status_email_failure_does_not_undo_transition(self, _send_mail):
        self.add_cart()
        created = self.create_order().json()
        with self.captureOnCommitCallbacks(execute=True):
            order = capture_order_stock(
                Order.objects.get(reference=created["reference"])
            )
            order = transition_order_status(order, Order.Status.PROCESSING)

        order.refresh_from_db()
        self.assertEqual(order.status, Order.Status.PROCESSING)

    def test_customer_cannot_read_another_customers_order(self):
        self.add_cart()
        created = self.create_order().json()
        self.client.force_login(self.other)
        response = self.client.get(
            reverse("orders:customer-detail", args=[created["reference"]])
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_customer_order_list_contains_the_created_order(self):
        self.add_cart()
        created = self.create_order()

        response = self.client.get(reverse("orders:customer-list"))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()), 1)
        self.assertEqual(
            response.json()[0]["reference"],
            created.json()["reference"],
        )
