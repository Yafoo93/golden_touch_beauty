from datetime import time
from decimal import Decimal
from django.utils import timezone
from django.core.exceptions import ValidationError

from django.test import TestCase
from django.urls import reverse
from rest_framework import status

from accounts.models import User
from auditlog.models import AuditLog
from branches.models import Branch, BranchStaffAssignment
from inventory.models import BranchInventory, StockMovement
from products.models import Product, ProductCategory, ProductVariant
from services.models import Service, ServiceBranchAvailability, ServiceCategory
from .models import POSPaymentEntry, POSSale, POSSaleLine


class POSWorkspaceApiTests(TestCase):
    def setUp(self):
        self.makola = Branch.objects.create(
            name="POS Makola", code="POS-MAKOLA", address="Accra",
            telephone_number="+233200000701", opening_days=["monday"],
            opening_time=time(7, 30), closing_time=time(17),
        )
        self.tse_addo = Branch.objects.create(
            name="POS Tse Addo", code="POS-TSE", address="Accra",
            telephone_number="+233200000702", opening_days=["monday"],
            opening_time=time(7, 30), closing_time=time(19),
        )
        self.owner = User.objects.create_superuser(
            email="pos-owner@example.com", phone_number="+233200000703",
            full_name="POS Owner", password="OwnerPass123!",
        )
        self.cashier = User.objects.create_user(
            email="pos-cashier@example.com", phone_number="+233200000704",
            full_name="POS Cashier", password="CashierPass123!", is_staff=True,
        )
        self.stock_manager = User.objects.create_user(
            email="pos-stock@example.com", phone_number="+233200000705",
            full_name="POS Stock", password="StockPass123!", is_staff=True,
        )
        self.manager = User.objects.create_user(
            email="pos-manager@example.com", phone_number="+233200000711",
            full_name="POS Manager", password="ManagerPass123!", is_staff=True,
        )
        BranchStaffAssignment.objects.create(
            branch=self.makola, staff=self.cashier,
            roles=[BranchStaffAssignment.Role.CASHIER], assigned_by=self.owner,
        )
        BranchStaffAssignment.objects.create(
            branch=self.makola, staff=self.stock_manager,
            roles=[BranchStaffAssignment.Role.STOCK_MANAGER], assigned_by=self.owner,
        )
        BranchStaffAssignment.objects.create(
            branch=self.makola, staff=self.manager,
            roles=[BranchStaffAssignment.Role.MANAGER], assigned_by=self.owner,
        )
        product_category = ProductCategory.objects.create(name="POS Products", slug="pos-products")
        product = Product.objects.create(
            category=product_category, name="POS Face Cream", slug="pos-face-cream",
            description="Test", is_active=True, is_published=True,
        )
        variant = ProductVariant.objects.create(
            product=product, name="Standard", sku="POS-CREAM-1",
            selling_price="45.00", cost_price="20.00",
        )
        BranchInventory.objects.create(
            branch=self.makola, product_variant=variant,
            quantity_on_hand=5, quantity_reserved=1, reorder_level=1,
        )
        service_category = ServiceCategory.objects.create(name="POS Services", slug="pos-services")
        service = Service.objects.create(
            category=service_category, name="POS Facial", slug="pos-facial",
            short_description="Test", description="Test", price="80.00",
            duration_minutes=60, is_active=True, is_published=True,
        )
        ServiceBranchAvailability.objects.create(branch=self.makola, service=service)

    def test_cashier_receives_assigned_branch_products_and_services(self):
        self.client.force_login(self.cashier)
        response = self.client.get(reverse("pos:workspace"))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()["selected_branch"], str(self.makola.pk))
        self.assertEqual([item["name"] for item in response.json()["products"]], ["POS Face Cream"])
        self.assertEqual(response.json()["products"][0]["available_quantity"], 4)
        self.assertEqual([item["name"] for item in response.json()["services"]], ["POS Facial"])

    def test_multiple_branch_user_must_explicitly_select_a_branch(self):
        self.client.force_login(self.owner)
        response = self.client.get(reverse("pos:workspace"))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsNone(response.json()["selected_branch"])
        self.assertEqual(response.json()["products"], [])
        self.assertEqual(response.json()["services"], [])
        self.assertEqual(
            {branch["id"] for branch in response.json()["branches"]},
            {str(self.makola.pk), str(self.tse_addo.pk)},
        )

    def test_anonymous_and_unassigned_staff_cannot_open_pos_workspace(self):
        anonymous_response = self.client.get(reverse("pos:workspace"))
        unassigned = User.objects.create_user(
            email="pos-unassigned@example.com", phone_number="+233200000708",
            full_name="Unassigned Cashier", password="CashierPass123!", is_staff=True,
        )
        self.client.force_login(unassigned)
        unassigned_response = self.client.get(reverse("pos:workspace"))

        self.assertIn(anonymous_response.status_code, (status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN))
        self.assertEqual(unassigned_response.status_code, status.HTTP_403_FORBIDDEN)

    def test_inactive_cashier_assignment_does_not_grant_pos_access(self):
        assignment = BranchStaffAssignment.objects.get(branch=self.makola, staff=self.cashier)
        assignment.is_active = False
        assignment.save(update_fields=["is_active", "updated_at"])
        self.client.force_login(self.cashier)
        response = self.client.get(reverse("pos:workspace"))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_cashier_cannot_select_unassigned_branch(self):
        self.client.force_login(self.cashier)
        response = self.client.get(reverse("pos:workspace"), {"branch": str(self.tse_addo.pk)})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_stock_manager_cannot_access_pos_catalogue(self):
        self.client.force_login(self.stock_manager)
        response = self.client.get(reverse("pos:workspace"))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_search_filters_both_catalogues(self):
        self.client.force_login(self.owner)
        response = self.client.get(reverse("pos:workspace"), {"branch": str(self.makola.pk), "search": "facial"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()["products"], [])
        self.assertEqual(len(response.json()["services"]), 1)

    def test_cashier_can_search_and_select_an_existing_customer(self):
        customer = User.objects.create_user(
            email="ama.customer@example.com", phone_number="+233200000709",
            full_name="Ama Customer", password="CustomerPass123!",
        )
        self.client.force_login(self.cashier)

        response = self.client.get(reverse("pos:customer-search"), {
            "branch": str(self.makola.pk), "search": "Ama",
        })

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()["results"], [{
            "id": str(customer.pk), "full_name": customer.full_name,
            "email": customer.email, "phone_number": customer.phone_number,
        }])

    def test_customer_search_rejects_unassigned_branch_and_excludes_staff(self):
        self.client.force_login(self.cashier)
        denied = self.client.get(reverse("pos:customer-search"), {
            "branch": str(self.tse_addo.pk), "search": "POS",
        })
        allowed = self.client.get(reverse("pos:customer-search"), {
            "branch": str(self.makola.pk), "search": "Cashier",
        })

        self.assertEqual(denied.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(allowed.status_code, status.HTTP_200_OK)
        self.assertEqual(allowed.json()["results"], [])

    def test_cashier_history_is_limited_to_assigned_branches(self):
        POSSale.objects.create(
            branch=self.makola, cashier=self.cashier, status=POSSale.Status.COMPLETED,
            payment_status="paid", total_amount="125.00", item_count=2,
            completed_at=timezone.now(),
        )
        POSSale.objects.create(branch=self.tse_addo, cashier=self.owner, status=POSSale.Status.COMPLETED, total_amount="90.00")
        self.client.force_login(self.cashier)

        response = self.client.get(reverse("pos:sales"))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()["count"], 1)
        sale = response.json()["results"][0]
        self.assertEqual(sale["branch_code"], self.makola.code)
        self.assertEqual(sale["cashier_name"], self.cashier.full_name)
        self.assertEqual(sale["customer_name"], "Walk-in customer")

    def test_history_filters_status_date_and_search(self):
        completed = POSSale.objects.create(
            branch=self.makola, cashier=self.cashier, status=POSSale.Status.COMPLETED,
            total_amount="75.00", completed_at=timezone.now(),
        )
        POSSale.objects.create(branch=self.makola, cashier=self.cashier, status=POSSale.Status.DRAFT)
        self.client.force_login(self.owner)
        response = self.client.get(reverse("pos:sales"), {
            "branch": str(self.makola.pk), "status": "completed",
            "date_from": timezone.localdate().isoformat(),
            "date_to": timezone.localdate().isoformat(), "search": completed.reference,
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()["count"], 1)
        self.assertEqual(response.json()["results"][0]["reference"], completed.reference)

    def test_cashier_can_view_completed_sale_receipt_snapshot(self):
        sale = POSSale.objects.create(
            branch=self.makola, cashier=self.cashier, status=POSSale.Status.COMPLETED,
            payment_status="paid", total_amount="125.00", item_count=2,
            completed_at=timezone.now(),
        )
        POSSaleLine.objects.create(
            sale=sale, item_type=POSSaleLine.ItemType.PRODUCT,
            item_reference="variant-1", name="POS Face Cream", option_name="Standard",
            sku="POS-CREAM-1", quantity=2, unit_price="45.00", line_total="90.00",
        )
        POSSaleLine.objects.create(
            sale=sale, item_type=POSSaleLine.ItemType.SERVICE,
            item_reference="service-1", name="POS Facial", quantity=1,
            unit_price="35.00", line_total="35.00",
        )
        POSPaymentEntry.objects.create(sale=sale, method="cash", amount="125.00")
        self.client.force_login(self.cashier)

        response = self.client.get(reverse("pos:sale-detail", args=[sale.reference]))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()["receipt_reference"], sale.receipt_reference)
        self.assertEqual(len(response.json()["lines"]), 2)
        self.assertEqual(response.json()["payments"][0]["method"], "cash")

    def test_one_sale_can_contain_product_and_service_lines(self):
        sale = POSSale.objects.create(
            branch=self.makola, cashier=self.cashier, status=POSSale.Status.DRAFT,
            total_amount="170.00", item_count=3,
        )
        POSSaleLine.objects.create(
            sale=sale, item_type=POSSaleLine.ItemType.PRODUCT,
            item_reference="variant-1", name="POS Face Cream", option_name="Standard",
            sku="POS-CREAM-1", quantity=2, unit_price="45.00", line_total="90.00",
        )
        POSSaleLine.objects.create(
            sale=sale, item_type=POSSaleLine.ItemType.SERVICE,
            item_reference="service-1", name="POS Facial", option_name="60 minutes",
            quantity=1, unit_price="80.00", line_total="80.00",
        )

        self.assertEqual(sale.lines.filter(item_type=POSSaleLine.ItemType.PRODUCT).count(), 1)
        self.assertEqual(sale.lines.filter(item_type=POSSaleLine.ItemType.SERVICE).count(), 1)
        self.assertEqual(sum(line.line_total for line in sale.lines.all()), Decimal("170.00"))

    def test_cashier_records_a_split_payment_for_product_and_service_sale(self):
        self.client.force_login(self.cashier)
        workspace = self.client.get(reverse("pos:workspace")).json()
        product = workspace["products"][0]
        service = workspace["services"][0]

        response = self.client.post(reverse("pos:sales"), {
            "branch": str(self.makola.pk),
            "customer": None,
            "lines": [
                {"item_type": "product", "item_reference": product["id"], "quantity": 2},
                {"item_type": "service", "item_reference": service["id"], "quantity": 1},
            ],
            "payments": [
                {"method": "cash", "amount": "70.00", "reference": ""},
                {"method": "mobile_money", "amount": "100.00", "reference": "MOMO-123"},
            ],
        }, content_type="application/json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.json()["total_amount"], "170.00")
        self.assertEqual(response.json()["paid_amount"], "170.00")
        self.assertEqual(response.json()["outstanding_amount"], "0.00")
        self.assertEqual(response.json()["payment_status"], "paid")
        sale = POSSale.objects.get(reference=response.json()["reference"])
        self.assertEqual(sale.status, POSSale.Status.COMPLETED)
        self.assertEqual(sale.cashier, self.cashier)
        self.assertEqual(sale.branch, self.makola)
        self.assertEqual(response.json()["cashier_id"], str(self.cashier.pk))
        self.assertEqual(response.json()["branch_id"], str(self.makola.pk))
        self.assertTrue(response.json()["receipt_reference"].startswith("GTR-POS-"))
        self.assertEqual(set(sale.payment_entries.values_list("method", flat=True)), {"cash", "mobile_money"})
        self.assertIsNone(sale.customer)

    def test_pos_sale_deducts_product_stock_at_sale_branch_and_records_movement(self):
        self.client.force_login(self.cashier)
        product = self.client.get(reverse("pos:workspace")).json()["products"][0]
        inventory = BranchInventory.objects.get(
            branch=self.makola, product_variant_id=product["id"],
        )

        response = self.client.post(reverse("pos:sales"), {
            "branch": str(self.makola.pk),
            "lines": [{"item_type": "product", "item_reference": product["id"], "quantity": 2}],
            "payments": [{"method": "cash", "amount": "90.00", "reference": ""}],
        }, content_type="application/json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        inventory.refresh_from_db()
        self.assertEqual(inventory.quantity_on_hand, 3)
        self.assertEqual(inventory.quantity_reserved, 1)
        self.assertEqual(inventory.quantity_available, 2)
        movement = StockMovement.objects.get(reference_id=response.json()["reference"])
        self.assertEqual(movement.movement_type, StockMovement.MovementType.SALE)
        self.assertEqual(movement.quantity_on_hand_change, -2)
        self.assertEqual(movement.quantity_on_hand_after, 3)
        self.assertEqual(movement.performed_by, self.cashier)

    def test_service_only_pos_sale_does_not_change_stock(self):
        self.client.force_login(self.cashier)
        service = self.client.get(reverse("pos:workspace")).json()["services"][0]
        inventory = BranchInventory.objects.get(branch=self.makola)
        before = inventory.quantity_on_hand

        response = self.client.post(reverse("pos:sales"), {
            "branch": str(self.makola.pk),
            "lines": [{"item_type": "service", "item_reference": service["id"], "quantity": 1}],
            "payments": [{"method": "cash", "amount": "80.00", "reference": ""}],
        }, content_type="application/json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        inventory.refresh_from_db()
        self.assertEqual(inventory.quantity_on_hand, before)
        self.assertFalse(StockMovement.objects.filter(reference_id=response.json()["reference"]).exists())

    def test_insufficient_pos_stock_rolls_back_sale_and_payments(self):
        self.client.force_login(self.cashier)
        product = self.client.get(reverse("pos:workspace")).json()["products"][0]

        response = self.client.post(reverse("pos:sales"), {
            "branch": str(self.makola.pk),
            "lines": [{"item_type": "product", "item_reference": product["id"], "quantity": 5}],
            "payments": [{"method": "cash", "amount": "225.00", "reference": ""}],
        }, content_type="application/json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(POSSale.objects.count(), 0)
        self.assertEqual(POSPaymentEntry.objects.count(), 0)
        self.assertEqual(StockMovement.objects.count(), 0)

    def test_cashier_records_partial_payment_for_existing_customer(self):
        customer = User.objects.create_user(
            email="partial.customer@example.com", phone_number="+233200000710",
            full_name="Partial Customer", password="CustomerPass123!",
        )
        self.client.force_login(self.cashier)
        service = self.client.get(reverse("pos:workspace")).json()["services"][0]
        response = self.client.post(reverse("pos:sales"), {
            "branch": str(self.makola.pk), "customer": str(customer.pk),
            "lines": [{"item_type": "service", "item_reference": service["id"], "quantity": 1}],
            "payments": [{"method": "bank_transfer", "amount": "30.00", "reference": "BANK-123"}],
        }, content_type="application/json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.json()["payment_status"], "partially_paid")
        self.assertEqual(response.json()["outstanding_amount"], "50.00")
        self.assertEqual(POSSale.objects.get(reference=response.json()["reference"]).customer, customer)

    def test_electronic_payment_requires_reference_and_payment_cannot_exceed_total(self):
        self.client.force_login(self.cashier)
        service = self.client.get(reverse("pos:workspace")).json()["services"][0]
        base = {
            "branch": str(self.makola.pk),
            "lines": [{"item_type": "service", "item_reference": service["id"], "quantity": 1}],
        }
        missing_reference = self.client.post(reverse("pos:sales"), {
            **base, "payments": [{"method": "card", "amount": "80.00", "reference": ""}],
        }, content_type="application/json")
        overpayment = self.client.post(reverse("pos:sales"), {
            **base, "payments": [{"method": "cash", "amount": "81.00", "reference": ""}],
        }, content_type="application/json")

        self.assertEqual(missing_reference.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(overpayment.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(POSSale.objects.count(), 0)

    def test_cashier_cannot_view_another_branch_sale_or_draft_receipt(self):
        other_sale = POSSale.objects.create(branch=self.tse_addo, cashier=self.owner, status=POSSale.Status.COMPLETED)
        draft = POSSale.objects.create(branch=self.makola, cashier=self.cashier, status=POSSale.Status.DRAFT)
        self.client.force_login(self.cashier)
        self.assertEqual(self.client.get(reverse("pos:sale-detail", args=[other_sale.reference])).status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(self.client.get(reverse("pos:sale-detail", args=[draft.reference])).status_code, status.HTTP_404_NOT_FOUND)

    def test_completed_sale_cannot_be_saved_without_cashier_attribution(self):
        with self.assertRaises(ValidationError):
            POSSale.objects.create(
                branch=self.makola, status=POSSale.Status.COMPLETED,
                total_amount="10.00", completed_at=timezone.now(),
            )

    def test_completed_sale_is_read_only_through_api_and_model(self):
        sale = POSSale.objects.create(
            branch=self.makola, cashier=self.cashier,
            status=POSSale.Status.COMPLETED, payment_status="paid",
            total_amount="80.00", completed_at=timezone.now(),
        )
        self.client.force_login(self.cashier)

        patch_response = self.client.patch(
            reverse("pos:sale-detail", args=[sale.reference]),
            {"total_amount": "1.00"}, content_type="application/json",
        )
        delete_response = self.client.delete(reverse("pos:sale-detail", args=[sale.reference]))
        sale.total_amount = Decimal("1.00")

        self.assertEqual(patch_response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
        self.assertEqual(delete_response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
        with self.assertRaises(ValidationError):
            sale.save()
        with self.assertRaises(ValidationError):
            sale.delete()
        sale.refresh_from_db()
        self.assertEqual(sale.total_amount, Decimal("80.00"))

    def test_manager_refund_restores_stock_updates_payments_and_writes_audit_history(self):
        self.client.force_login(self.cashier)
        product = self.client.get(reverse("pos:workspace")).json()["products"][0]
        created = self.client.post(reverse("pos:sales"), {
            "branch": str(self.makola.pk),
            "lines": [{"item_type": "product", "item_reference": product["id"], "quantity": 2}],
            "payments": [{"method": "cash", "amount": "90.00", "reference": ""}],
        }, content_type="application/json")
        reference = created.json()["reference"]
        inventory = BranchInventory.objects.get(branch=self.makola, product_variant_id=product["id"])
        self.assertEqual(inventory.quantity_on_hand, 3)

        self.client.force_login(self.manager)
        response = self.client.post(reverse("pos:sale-correction", args=[reference]), {
            "correction_type": "refund",
            "reason": "Customer returned the unopened product at the clinic.",
        }, content_type="application/json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()["status"], POSSale.Status.REFUNDED)
        self.assertFalse(response.json()["can_correct"])
        self.assertEqual(len(response.json()["corrections"]), 1)
        inventory.refresh_from_db()
        self.assertEqual(inventory.quantity_on_hand, 5)
        sale = POSSale.objects.get(reference=reference)
        self.assertEqual(sale.payment_status, "refunded")
        self.assertEqual(list(sale.payment_entries.values_list("status", flat=True)), ["refunded"])
        movement = StockMovement.objects.get(reference_type="pos_sale_correction", reference_id=reference)
        self.assertEqual(movement.quantity_on_hand_change, 2)
        audit = AuditLog.objects.get(record_type="pos_sale", record_id=reference)
        self.assertEqual(audit.action, "pos.sale_refunded")
        self.assertEqual(audit.actor, self.manager)
        self.assertEqual(audit.branch, self.makola)
        self.assertEqual(audit.reason, "Customer returned the unopened product at the clinic.")

    def test_cashier_cannot_correct_sale_and_reason_is_required(self):
        sale = POSSale.objects.create(
            branch=self.makola, cashier=self.cashier, status=POSSale.Status.COMPLETED,
            payment_status="paid", total_amount="80.00", completed_at=timezone.now(),
        )
        self.client.force_login(self.cashier)
        denied = self.client.post(reverse("pos:sale-correction", args=[sale.reference]), {
            "correction_type": "reversal", "reason": "Cashier attempted correction.",
        }, content_type="application/json")
        self.client.force_login(self.manager)
        invalid = self.client.post(reverse("pos:sale-correction", args=[sale.reference]), {
            "correction_type": "reversal", "reason": "short",
        }, content_type="application/json")

        self.assertEqual(denied.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(invalid.status_code, status.HTTP_400_BAD_REQUEST)
        sale.refresh_from_db()
        self.assertEqual(sale.status, POSSale.Status.COMPLETED)
        self.assertFalse(AuditLog.objects.filter(record_id=sale.reference).exists())

    def test_completed_sale_can_only_be_corrected_once(self):
        sale = POSSale.objects.create(
            branch=self.makola, cashier=self.cashier, status=POSSale.Status.COMPLETED,
            payment_status="paid", total_amount="80.00", completed_at=timezone.now(),
        )
        self.client.force_login(self.manager)
        first = self.client.post(reverse("pos:sale-correction", args=[sale.reference]), {
            "correction_type": "reversal", "reason": "Sale was entered twice by mistake.",
        }, content_type="application/json")
        second = self.client.post(reverse("pos:sale-correction", args=[sale.reference]), {
            "correction_type": "reversal", "reason": "Attempting the same correction again.",
        }, content_type="application/json")

        self.assertEqual(first.status_code, status.HTTP_200_OK)
        self.assertEqual(second.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(AuditLog.objects.filter(record_id=sale.reference).count(), 1)

    def test_owner_end_of_day_summarizes_cashiers_and_payment_methods(self):
        other_cashier = User.objects.create_user(
            email="pos-cashier-two@example.com", phone_number="+233200000706",
            full_name="Second Cashier", password="CashierPass123!", is_staff=True,
        )
        BranchStaffAssignment.objects.create(
            branch=self.makola, staff=other_cashier,
            roles=[BranchStaffAssignment.Role.CASHIER], assigned_by=self.owner,
        )
        first = POSSale.objects.create(
            branch=self.makola, cashier=self.cashier, status=POSSale.Status.COMPLETED,
            total_amount="100.00", item_count=2, completed_at=timezone.now(),
        )
        second = POSSale.objects.create(
            branch=self.makola, cashier=other_cashier, status=POSSale.Status.COMPLETED,
            total_amount="50.00", item_count=1, completed_at=timezone.now(),
        )
        refunded = POSSale.objects.create(
            branch=self.makola, cashier=self.cashier, status=POSSale.Status.REFUNDED,
            total_amount="30.00", completed_at=timezone.now(),
        )
        POSPaymentEntry.objects.create(sale=first, method="cash", amount="100.00")
        POSPaymentEntry.objects.create(sale=second, method="card", amount="50.00")
        POSPaymentEntry.objects.create(sale=refunded, method="cash", amount="30.00")
        self.client.force_login(self.owner)

        response = self.client.get(reverse("pos:end-of-day"), {
            "date": timezone.localdate().isoformat(), "branch": str(self.makola.pk),
        })

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()["scope"], "team")
        self.assertEqual(response.json()["summary"], {
            "sale_count": 2, "item_count": 3, "gross_total": "150.00",
            "payment_total": "150.00", "difference": "0.00",
        })
        self.assertEqual({item["method"] for item in response.json()["payment_methods"]}, {"cash", "card"})
        self.assertEqual({item["cashier_name"] for item in response.json()["cashiers"]}, {self.cashier.full_name, other_cashier.full_name})

    def test_cashier_end_of_day_only_contains_their_sales(self):
        other_cashier = User.objects.create_user(
            email="pos-private-cashier@example.com", phone_number="+233200000707",
            full_name="Private Cashier", password="CashierPass123!", is_staff=True,
        )
        first = POSSale.objects.create(
            branch=self.makola, cashier=self.cashier, status=POSSale.Status.COMPLETED,
            total_amount="70.00", item_count=1, completed_at=timezone.now(),
        )
        POSSale.objects.create(
            branch=self.makola, cashier=other_cashier, status=POSSale.Status.COMPLETED,
            total_amount="500.00", item_count=5, completed_at=timezone.now(),
        )
        POSPaymentEntry.objects.create(sale=first, method="cash", amount="60.00")
        self.client.force_login(self.cashier)

        response = self.client.get(reverse("pos:end-of-day"))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()["scope"], "cashier")
        self.assertEqual(response.json()["summary"]["gross_total"], "70.00")
        self.assertEqual(response.json()["summary"]["payment_total"], "60.00")
        self.assertEqual(response.json()["summary"]["difference"], "10.00")
        self.assertEqual([item["cashier_name"] for item in response.json()["cashiers"]], [self.cashier.full_name])

    def test_cashier_cannot_request_end_of_day_for_unassigned_branch(self):
        self.client.force_login(self.cashier)
        response = self.client.get(reverse("pos:end-of-day"), {"branch": str(self.tse_addo.pk)})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
