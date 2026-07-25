from datetime import time
from decimal import Decimal

from django.test import TestCase
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.urls import reverse
from rest_framework import status

from branches.models import Branch, BranchStaffAssignment
from products.models import Product, ProductCategory, ProductVariant

from .models import BranchInventory, StockMovement


User = get_user_model()


class PickupBranchOptionsApiTests(TestCase):
    def setUp(self):
        self.makola = self._branch("Makola", "MAKOLA")
        self.tse_addo = self._branch("Tse Addo", "TSE_ADDO")
        category = ProductCategory.objects.create(
            name="Face Creams",
            slug="face-creams",
            is_active=True,
        )
        product = Product.objects.create(
            category=category,
            name="Face Cream",
            slug="face-cream",
            description="Test product",
            is_active=True,
            is_published=True,
        )
        self.variant = ProductVariant.objects.create(
            product=product,
            name="Standard",
            sku="FACE-CREAM-STD",
            selling_price=Decimal("100.00"),
            cost_price=Decimal("50.00"),
            is_active=True,
        )
        BranchInventory.objects.create(
            branch=self.makola,
            product_variant=self.variant,
            quantity_on_hand=10,
            quantity_reserved=2,
            is_available=True,
        )
        BranchInventory.objects.create(
            branch=self.tse_addo,
            product_variant=self.variant,
            quantity_on_hand=2,
            quantity_reserved=2,
            is_available=True,
        )

    @staticmethod
    def _branch(name, code):
        return Branch.objects.create(
            name=name,
            code=code,
            address=f"{name}, Accra",
            telephone_number="+233000000000",
            opening_days=["monday", "saturday"],
            opening_time=time(7, 30),
            closing_time=time(17, 0),
            is_active=True,
        )

    def test_only_branch_with_sufficient_available_stock_is_eligible(self):
        response = self.client.post(
            reverse("branches:pickup-options"),
            {"items": [{"sku": self.variant.sku, "quantity": 3}]},
            content_type="application/json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        options = {
            option["branch"]["code"]: option
            for option in response.json()["results"]
        }
        self.assertTrue(options["MAKOLA"]["eligible"])
        self.assertFalse(options["TSE_ADDO"]["eligible"])
        self.assertNotIn("quantity_on_hand", str(response.json()))

    def test_duplicate_lines_are_aggregated_before_stock_check(self):
        response = self.client.post(
            reverse("branches:pickup-options"),
            {
                "items": [
                    {"sku": self.variant.sku, "quantity": 5},
                    {"sku": self.variant.sku, "quantity": 4},
                ]
            },
            content_type="application/json",
        )

        makola = next(
            option
            for option in response.json()["results"]
            if option["branch"]["code"] == "MAKOLA"
        )
        self.assertFalse(makola["eligible"])

    def test_unknown_variant_uses_standard_validation_error(self):
        response = self.client.post(
            reverse("branches:pickup-options"),
            {"items": [{"sku": "UNKNOWN", "quantity": 1}]},
            content_type="application/json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.json()["error"]["code"], "validation_error")


class ManagementInventoryApiTests(TestCase):
    def setUp(self):
        self.makola = PickupBranchOptionsApiTests._branch(
            "Makola inventory management", "MAKOLA-INV-MGMT"
        )
        self.tse_addo = PickupBranchOptionsApiTests._branch(
            "Tse Addo inventory management", "TSE-ADDO-INV-MGMT"
        )
        category = ProductCategory.objects.create(
            name="Inventory management products",
            slug="inventory-management-products",
        )
        product = Product.objects.create(
            category=category,
            name="Inventory Management Cream",
            slug="inventory-management-cream",
            description="Inventory dashboard test.",
        )
        self.variant = ProductVariant.objects.create(
            product=product,
            name="Standard",
            sku="INV-MGMT-CREAM",
            selling_price="150.00",
            cost_price="80.00",
        )
        BranchInventory.objects.create(
            branch=self.makola,
            product_variant=self.variant,
            quantity_on_hand=10,
            quantity_reserved=2,
            reorder_level=3,
        )
        BranchInventory.objects.create(
            branch=self.tse_addo,
            product_variant=self.variant,
            quantity_on_hand=4,
            quantity_reserved=2,
            reorder_level=2,
        )
        self.owner = User.objects.create_superuser(
            email="inventory-owner@example.com",
            phone_number="+233241000081",
            full_name="Inventory Owner",
            password="OwnerPass123!",
        )
        self.stock_manager = User.objects.create_user(
            email="inventory-manager@example.com",
            phone_number="+233241000082",
            full_name="Inventory Manager",
            password="ManagerPass123!",
            is_staff=True,
        )
        BranchStaffAssignment.objects.create(
            branch=self.makola,
            staff=self.stock_manager,
            roles=[BranchStaffAssignment.Role.STOCK_MANAGER],
            assigned_by=self.owner,
        )
        for inventory in BranchInventory.objects.filter(product_variant=self.variant):
            StockMovement.objects.create(
                inventory=inventory,
                movement_type=StockMovement.MovementType.OPENING,
                quantity_on_hand_change=inventory.quantity_on_hand,
                quantity_on_hand_after=inventory.quantity_on_hand,
                quantity_reserved_after=inventory.quantity_reserved,
                note="Test opening balance.",
                performed_by=self.owner,
            )

    def test_owner_sees_stock_for_all_branches_and_can_filter_low_stock(self):
        self.client.force_login(self.owner)
        listing = self.client.get(reverse("inventory:management-list"))
        low_stock = self.client.get(
            reverse("inventory:management-list"), {"low_stock": "true"}
        )

        self.assertEqual(listing.status_code, status.HTTP_200_OK)
        self.assertEqual(len(listing.json()), 2)
        self.assertEqual(
            {item["branch_code"] for item in low_stock.json()},
            {self.tse_addo.code},
        )
        self.assertEqual(low_stock.json()[0]["quantity_available"], 2)
        self.assertTrue(low_stock.json()[0]["is_low_stock"])

    def test_stock_manager_only_sees_assigned_branch(self):
        self.client.force_login(self.stock_manager)
        response = self.client.get(reverse("inventory:management-list"))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()), 1)
        self.assertEqual(response.json()[0]["branch_id"], str(self.makola.id))

    def test_unassigned_customer_cannot_view_inventory(self):
        customer = User.objects.create_user(
            email="inventory-customer@example.com",
            phone_number="+233241000083",
            full_name="Inventory Customer",
            password="CustomerPass123!",
        )
        self.client.force_login(customer)

        response = self.client.get(reverse("inventory:management-list"))

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_owner_can_view_variant_history_across_branches(self):
        self.client.force_login(self.owner)

        response = self.client.get(
            reverse("inventory:management-variant-history", args=[self.variant.id])
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()["variant"]["sku"], self.variant.sku)
        self.assertEqual(len(response.json()["current_stock"]), 2)
        self.assertEqual(len(response.json()["movements"]), 2)
        self.assertEqual(
            {item["branch_id"] for item in response.json()["movements"]},
            {str(self.makola.id), str(self.tse_addo.id)},
        )

    def test_stock_manager_history_is_limited_to_assigned_branch(self):
        self.client.force_login(self.stock_manager)

        response = self.client.get(
            reverse("inventory:management-variant-history", args=[self.variant.id])
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()["current_stock"]), 1)
        self.assertEqual(len(response.json()["movements"]), 1)
        self.assertEqual(
            response.json()["movements"][0]["branch_id"], str(self.makola.id)
        )

    def test_stock_movements_are_append_only(self):
        movement = StockMovement.objects.filter(
            inventory__product_variant=self.variant
        ).first()

        movement.note = "Attempted modification"
        with self.assertRaises(ValidationError):
            movement.save()
        with self.assertRaises(ValidationError):
            StockMovement.objects.filter(id=movement.id).update(
                note="Attempted bulk modification"
            )
        with self.assertRaises(ValidationError):
            movement.delete()
        with self.assertRaises(ValidationError):
            StockMovement.objects.filter(id=movement.id).delete()

        movement.refresh_from_db()
        self.assertEqual(movement.note, "Test opening balance.")

    def test_stock_manager_can_adjust_assigned_branch_stock(self):
        self.client.force_login(self.stock_manager)

        response = self.client.post(
            reverse("inventory:management-adjustment"),
            {
                "branch_id": str(self.makola.id),
                "variant_id": str(self.variant.id),
                "quantity_change": -3,
                "reason": "Three damaged containers removed after inspection.",
            },
            content_type="application/json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        inventory = BranchInventory.objects.get(
            branch=self.makola, product_variant=self.variant
        )
        self.assertEqual(inventory.quantity_on_hand, 7)
        movement = inventory.movements.first()
        self.assertEqual(movement.quantity_on_hand_change, -3)
        self.assertEqual(movement.quantity_on_hand_after, 7)
        self.assertEqual(movement.performed_by, self.stock_manager)

    def test_stock_manager_cannot_adjust_unassigned_branch(self):
        self.client.force_login(self.stock_manager)

        response = self.client.post(
            reverse("inventory:management-adjustment"),
            {
                "branch_id": str(self.tse_addo.id),
                "variant_id": str(self.variant.id),
                "quantity_change": 2,
                "reason": "Received replacement stock.",
            },
            content_type="application/json",
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(
            BranchInventory.objects.get(
                branch=self.tse_addo, product_variant=self.variant
            ).quantity_on_hand,
            4,
        )

    def test_adjustment_cannot_reduce_stock_below_reserved_quantity(self):
        self.client.force_login(self.owner)

        response = self.client.post(
            reverse("inventory:management-adjustment"),
            {
                "branch_id": str(self.makola.id),
                "variant_id": str(self.variant.id),
                "quantity_change": -9,
                "reason": "Attempt to remove too much stock.",
            },
            content_type="application/json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            BranchInventory.objects.get(
                branch=self.makola, product_variant=self.variant
            ).quantity_on_hand,
            10,
        )

    def test_database_prevents_negative_stock_even_if_api_is_bypassed(self):
        inventory = BranchInventory.objects.get(
            branch=self.makola, product_variant=self.variant
        )

        with self.assertRaises(IntegrityError), transaction.atomic():
            BranchInventory.objects.filter(id=inventory.id).update(
                quantity_on_hand=-1
            )

        inventory.refresh_from_db()
        self.assertEqual(inventory.quantity_on_hand, 10)
