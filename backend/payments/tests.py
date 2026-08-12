from django.contrib.auth import get_user_model
from django.core import mail
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from rest_framework import status

from branches.models import Branch
from orders.models import Order, OrderItem
from products.models import Product, ProductCategory, ProductVariant

from .models import Invoice, Payment, Receipt
from .services import issue_invoice_for_source, issue_receipt_for_verified_payment


User = get_user_model()


class ReceiptWorkflowTests(TestCase):
    def setUp(self):
        self.customer = User.objects.create_user(
            email="receipt@example.com",
            phone_number="+233241000501",
            full_name="Receipt Customer",
            password="CustomerPass123!",
        )
        self.other = User.objects.create_user(
            email="receipt-other@example.com",
            phone_number="+233241000502",
            full_name="Other Customer",
            password="CustomerPass123!",
        )
        self.branch = Branch.objects.create(
            name="Receipt Makola",
            code="RECEIPT-MAKOLA",
            address="Accra",
            telephone_number="+233241370429",
            opening_days=["monday"],
            opening_time="07:30",
            closing_time="17:00",
        )
        category = ProductCategory.objects.create(
            name="Receipt products", slug="receipt-products"
        )
        product = Product.objects.create(
            category=category,
            name="Receipt Face Serum",
            slug="receipt-face-serum",
            description="Test serum",
            is_active=True,
            is_published=True,
        )
        variant = ProductVariant.objects.create(
            product=product,
            name="30 ml",
            sku="RECEIPT-SERUM-30",
            selling_price="75.00",
            cost_price="30.00",
        )
        self.order = Order.objects.create(
            branch=self.branch,
            customer=self.customer,
            status=Order.Status.PAID,
            payment_status="paid",
            subtotal="150.00",
            total_amount="150.00",
            recipient_name=self.customer.full_name,
            recipient_phone=self.customer.phone_number,
            paid_at=timezone.now(),
        )
        OrderItem.objects.create(
            order=self.order,
            product_variant=variant,
            product_name=product.name,
            product_slug=product.slug,
            variant_name=variant.name,
            sku=variant.sku,
            unit_price="75.00",
            quantity=2,
            line_total="150.00",
        )
        self.payment = Payment.objects.create(
            branch=self.branch,
            customer=self.customer,
            order=self.order,
            provider="paystack",
            provider_reference="PAYSTACK-VERIFIED-001",
            method="mobile_money",
            status=Payment.Status.SUCCEEDED,
            amount="150.00",
            currency="GHS",
            paid_at=self.order.paid_at,
        )

    def test_verified_payment_creates_one_receipt_and_email(self):
        with self.captureOnCommitCallbacks(execute=True):
            receipt = issue_receipt_for_verified_payment(self.payment)
            repeated = issue_receipt_for_verified_payment(self.payment)

        self.assertEqual(receipt.pk, repeated.pk)
        self.assertEqual(Receipt.objects.count(), 1)
        invoice = Invoice.objects.get(order=self.order)
        self.assertEqual(invoice.status, Invoice.Status.PAID)
        self.assertEqual(invoice.paid_at, self.payment.paid_at)
        receipt.refresh_from_db()
        self.assertIsNotNone(receipt.email_sent_at)
        self.assertEqual(receipt.source_reference, self.order.reference)
        self.assertEqual(receipt.line_items[0]["quantity"], 2)
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn(receipt.reference, mail.outbox[0].subject)
        self.assertIn(
            f"/account/receipts/{receipt.reference}",
            mail.outbox[0].body,
        )

    def test_invoice_creation_is_idempotent_and_snapshots_source(self):
        invoice = issue_invoice_for_source(self.order)
        repeated = issue_invoice_for_source(self.order)

        self.assertEqual(invoice.pk, repeated.pk)
        self.assertEqual(Invoice.objects.count(), 1)
        self.assertEqual(invoice.status, Invoice.Status.OPEN)
        self.assertEqual(invoice.source_type, "order")
        self.assertEqual(invoice.source_reference, self.order.reference)
        self.assertEqual(invoice.total_amount, self.order.total_amount)
        self.assertEqual(invoice.line_items[0]["description"], "Receipt Face Serum (30 ml)")

    def test_pending_or_wrong_amount_payment_cannot_issue_receipt(self):
        self.payment.status = Payment.Status.PENDING
        self.payment.save(update_fields=["status", "updated_at"])
        with self.assertRaisesMessage(ValueError, "verified payment"):
            issue_receipt_for_verified_payment(self.payment)

        self.payment.status = Payment.Status.SUCCEEDED
        self.payment.amount = "149.00"
        self.payment.save(update_fields=["status", "amount", "updated_at"])
        with self.assertRaisesMessage(ValueError, "amount"):
            issue_receipt_for_verified_payment(self.payment)
        self.assertEqual(Receipt.objects.count(), 0)

    def test_customer_cannot_view_another_customers_receipt_or_payment_details(self):
        with self.captureOnCommitCallbacks(execute=True):
            receipt = issue_receipt_for_verified_payment(self.payment)
        self.client.force_login(self.customer)
        own = self.client.get(
            reverse("payments:receipt-detail", args=[receipt.reference])
        )
        self.assertEqual(own.status_code, status.HTTP_200_OK)
        self.assertEqual(own.json()["amount"], "150.00")
        self.assertEqual(own.json()["provider"], "paystack")

        self.client.force_login(self.other)
        hidden = self.client.get(
            reverse("payments:receipt-detail", args=[receipt.reference])
        )
        self.assertEqual(hidden.status_code, status.HTTP_404_NOT_FOUND)
        self.assertNotIn(self.payment.reference, hidden.content.decode())
        self.assertNotIn(self.payment.provider_reference, hidden.content.decode())
