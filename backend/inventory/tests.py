from datetime import time
from decimal import Decimal

from django.test import TestCase
from django.urls import reverse
from rest_framework import status

from branches.models import Branch
from products.models import Product, ProductCategory, ProductVariant

from .models import BranchInventory


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
