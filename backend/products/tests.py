import base64
import json

from django.test import TestCase
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from rest_framework import status

from branches.models import Branch
from inventory.models import BranchInventory
from auditlog.models import AuditLog

from .models import CustomerCartItem, Product, ProductCategory, ProductVariant, WishlistItem


User = get_user_model()


class FeaturedProductApiTests(TestCase):
    def test_featured_products_include_price_and_live_stock(self):
        branch = Branch.objects.create(
            name="Makola",
            code="MAKOLA",
            address="Accra",
            telephone_number="024 137 0429",
            opening_days=["monday"],
            opening_time="07:30",
            closing_time="17:00",
        )
        category = ProductCategory.objects.create(name="Creams", slug="creams")
        product = Product.objects.create(
            category=category,
            name="Face Cream",
            slug="face-cream",
            description="Daily moisturizer.",
            image_path="/images/face_cream.jpeg",
            is_featured=True,
            is_active=True,
            is_published=True,
        )
        variant = ProductVariant.objects.create(
            product=product,
            name="Standard",
            sku="FACE-CREAM",
            selling_price="180.00",
            cost_price="100.00",
        )
        BranchInventory.objects.create(
            branch=branch,
            product_variant=variant,
            quantity_on_hand=5,
        )

        response = self.client.get(reverse("products:featured"))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()), 1)
        self.assertEqual(response.json()[0]["price"], "180.00")
        self.assertEqual(response.json()[0]["sku"], "FACE-CREAM")
        self.assertIsNotNone(response.json()[0]["variant_id"])
        self.assertTrue(response.json()[0]["in_stock"])


class PublicProductCatalogueApiTests(TestCase):
    def setUp(self):
        self.branch = Branch.objects.create(
            name="Makola catalogue",
            code="MAKOLA-PRODUCTS",
            address="Accra",
            telephone_number="+233241370429",
            opening_days=["monday"],
            opening_time="07:30",
            closing_time="17:00",
        )
        self.creams = ProductCategory.objects.create(
            name="Face creams catalogue",
            slug="face-creams-catalogue",
            display_order=1,
        )
        self.oils = ProductCategory.objects.create(
            name="Face oils catalogue",
            slug="face-oils-catalogue",
            display_order=2,
        )
        self.stocked = self._product(
            category=self.creams,
            name="Radiance Face Cream",
            slug="radiance-face-cream",
            description="A daily brightening moisturiser.",
            price="180.00",
            sku="RAD-CREAM",
        )
        BranchInventory.objects.create(
            branch=self.branch,
            product_variant=self.stocked.variants.get(),
            quantity_on_hand=8,
            quantity_reserved=2,
        )
        self.preorder = self._product(
            category=self.oils,
            name="Restoring Face Oil",
            slug="restoring-face-oil",
            description="A nourishing botanical face serum and oil.",
            price="150.00",
            sku="REST-OIL",
            is_preorder=True,
        )
        self.out_of_stock = self._product(
            category=self.creams,
            name="Body Cream",
            slug="body-cream",
            description="A rich body moisturiser.",
            price="120.00",
            sku="BODY-CREAM",
        )
        hidden = self._product(
            category=self.creams,
            name="Draft Cream",
            slug="draft-cream",
            description="Not public.",
            price="90.00",
            sku="DRAFT-CREAM",
            is_published=False,
        )
        BranchInventory.objects.create(
            branch=self.branch,
            product_variant=hidden.variants.get(),
            quantity_on_hand=10,
        )

    def _product(
        self,
        *,
        category,
        name,
        slug,
        description,
        price,
        sku,
        is_preorder=False,
        is_published=True,
    ):
        product = Product.objects.create(
            category=category,
            name=name,
            slug=slug,
            brand="Golden Touch",
            description=description,
            image_path="/images/face_cream.jpeg",
            is_active=True,
            is_published=is_published,
        )
        ProductVariant.objects.create(
            product=product,
            name="Standard",
            sku=sku,
            selling_price=price,
            cost_price="50.00",
            is_preorder=is_preorder,
        )
        return product

    def test_list_returns_only_public_products_with_active_variants(self):
        response = self.client.get(reverse("products:list"))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            {product["slug"] for product in response.json()},
            {"radiance-face-cream", "restoring-face-oil", "body-cream"},
        )
        stocked = next(
            product
            for product in response.json()
            if product["slug"] == self.stocked.slug
        )
        self.assertEqual(stocked["availability"], "in_stock")
        self.assertTrue(stocked["in_stock"])
        self.assertNotIn("cost_price", stocked)

    def test_list_supports_search_and_category_filters(self):
        search = self.client.get(reverse("products:list"), {"search": "botanical"})
        category = self.client.get(
            reverse("products:list"),
            {"category": self.creams.slug},
        )

        self.assertEqual(
            [product["slug"] for product in search.json()],
            ["restoring-face-oil"],
        )
        self.assertEqual(
            {product["slug"] for product in category.json()},
            {"radiance-face-cream", "body-cream"},
        )

    def test_list_filters_each_availability_state(self):
        expected = {
            "in_stock": {"radiance-face-cream"},
            "preorder": {"restoring-face-oil"},
            "out_of_stock": {"body-cream"},
        }

        for availability, slugs in expected.items():
            with self.subTest(availability=availability):
                response = self.client.get(
                    reverse("products:list"),
                    {"availability": availability},
                )
                self.assertEqual(
                    {product["slug"] for product in response.json()},
                    slugs,
                )

    def test_categories_only_include_categories_with_public_products(self):
        empty = ProductCategory.objects.create(
            name="Empty product category",
            slug="empty-product-category",
        )

        response = self.client.get(reverse("products:categories"))
        slugs = {category["slug"] for category in response.json()}

        self.assertIn(self.creams.slug, slugs)
        self.assertIn(self.oils.slug, slugs)
        self.assertNotIn(empty.slug, slugs)

    def test_detail_returns_variants_prices_and_branch_availability(self):
        second_variant = ProductVariant.objects.create(
            product=self.stocked,
            name="Large",
            sku="RAD-CREAM-LARGE",
            selling_price="240.00",
            cost_price="90.00",
        )
        BranchInventory.objects.create(
            branch=self.branch,
            product_variant=second_variant,
            quantity_on_hand=4,
        )

        response = self.client.get(
            reverse("products:detail", args=[self.stocked.slug])
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()["name"], self.stocked.name)
        self.assertEqual(len(response.json()["variants"]), 2)
        standard = next(
            variant
            for variant in response.json()["variants"]
            if variant["sku"] == "RAD-CREAM"
        )
        self.assertEqual(standard["selling_price"], "180.00")
        self.assertEqual(standard["availability"], "in_stock")
        self.assertEqual(
            standard["available_at"][0]["branch_code"],
            self.branch.code,
        )
        self.assertNotIn("cost_price", standard)
        self.assertNotIn("quantity_on_hand", standard)

    def test_detail_hides_draft_products(self):
        response = self.client.get(
            reverse("products:detail", args=["draft-cream"])
        )

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class WishlistApiTests(TestCase):
    def setUp(self):
        category = ProductCategory.objects.create(
            name="Wishlist creams",
            slug="wishlist-creams",
        )
        self.product = Product.objects.create(
            category=category,
            name="Wishlist Face Cream",
            slug="wishlist-face-cream",
            description="A customer-saveable product.",
            image_path="/images/face_cream.jpeg",
            is_active=True,
            is_published=True,
        )
        ProductVariant.objects.create(
            product=self.product,
            name="Standard",
            sku="WISH-CREAM",
            selling_price="180.00",
            cost_price="100.00",
        )
        self.customer = User.objects.create_user(
            email="wishlist@example.com",
            phone_number="+233241000071",
            full_name="Wishlist Customer",
            password="CustomerPass123!",
        )
        self.other_customer = User.objects.create_user(
            email="wishlist-other@example.com",
            phone_number="+233241000072",
            full_name="Other Wishlist Customer",
            password="CustomerPass123!",
        )

    def test_wishlist_requires_authentication(self):
        response = self.client.get(reverse("products:wishlist"))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_customer_can_add_list_and_remove_product(self):
        self.client.force_login(self.customer)

        create = self.client.post(
            reverse("products:wishlist"),
            data={"product_slug": self.product.slug},
            content_type="application/json",
        )
        duplicate = self.client.post(
            reverse("products:wishlist"),
            data={"product_slug": self.product.slug},
            content_type="application/json",
        )
        listing = self.client.get(reverse("products:wishlist"))

        self.assertEqual(create.status_code, status.HTTP_201_CREATED)
        self.assertEqual(duplicate.status_code, status.HTTP_200_OK)
        self.assertEqual(WishlistItem.objects.count(), 1)
        self.assertEqual([item["slug"] for item in listing.json()], [self.product.slug])

        remove = self.client.delete(
            reverse("products:wishlist-item", args=[self.product.slug])
        )
        self.assertEqual(remove.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(
            WishlistItem.objects.filter(customer=self.customer).exists()
        )

    def test_customer_wishlist_is_private(self):
        WishlistItem.objects.create(
            customer=self.other_customer,
            product=self.product,
        )
        self.client.force_login(self.customer)

        response = self.client.get(reverse("products:wishlist"))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json(), [])


class CustomerCartMergeApiTests(TestCase):
    def setUp(self):
        self.branch = Branch.objects.create(
            name="Cart stock branch",
            code="CART-STOCK",
            address="Accra",
            telephone_number="+233241000090",
            opening_days=["monday"],
            opening_time="07:30",
            closing_time="17:00",
        )
        category = ProductCategory.objects.create(
            name="Customer cart products",
            slug="customer-cart-products",
        )
        product = Product.objects.create(
            category=category,
            name="Customer Cart Cream",
            slug="customer-cart-cream",
            description="A mergeable cart product.",
            image_path="/images/face_cream.jpeg",
            is_active=True,
            is_published=True,
        )
        self.variant = ProductVariant.objects.create(
            product=product,
            name="Standard",
            sku="CUSTOMER-CART-CREAM",
            selling_price="175.00",
            cost_price="90.00",
        )
        self.inventory = BranchInventory.objects.create(
            branch=self.branch,
            product_variant=self.variant,
            quantity_on_hand=5,
        )
        self.customer = User.objects.create_user(
            email="cart-merge@example.com",
            phone_number="+233241000091",
            full_name="Cart Merge Customer",
            password="CustomerPass123!",
        )

    def test_customer_cart_requires_authentication(self):
        response = self.client.get(reverse("products:customer-cart"))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_cart_changes_require_authentication(self):
        response = self.client.post(
            reverse("products:cart-validate"),
            {"items": []},
            content_type="application/json",
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_adding_cart_item_requires_authentication(self):
        response = self.client.post(
            reverse("products:customer-cart-items"),
            {"variant_id": str(self.variant.id), "quantity": 1},
            content_type="application/json",
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_customer_can_add_a_cart_item(self):
        self.client.force_login(self.customer)

        response = self.client.post(
            reverse("products:customer-cart-items"),
            {"variant_id": str(self.variant.id), "quantity": 2},
            content_type="application/json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()["items"][0]["quantity"], 2)
        self.assertEqual(response.json()["items"][0]["unit_price"], "175.00")
        self.assertEqual(
            CustomerCartItem.objects.get(
                customer=self.customer, variant=self.variant
            ).quantity,
            2,
        )

    def test_adding_existing_variant_increments_without_exceeding_stock(self):
        CustomerCartItem.objects.create(
            customer=self.customer,
            variant=self.variant,
            quantity=3,
        )
        self.client.force_login(self.customer)

        response = self.client.post(
            reverse("products:customer-cart-items"),
            {"variant_id": str(self.variant.id), "quantity": 4},
            content_type="application/json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()["items"][0]["quantity"], 5)
        self.assertEqual(
            response.json()["adjustments"][0]["code"], "quantity_reduced"
        )

    def test_changing_cart_quantity_requires_authentication(self):
        response = self.client.patch(
            reverse("products:customer-cart-item-detail", args=[self.variant.id]),
            {"quantity": 2},
            content_type="application/json",
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_customer_can_change_cart_item_quantity(self):
        CustomerCartItem.objects.create(
            customer=self.customer,
            variant=self.variant,
            quantity=1,
        )
        self.client.force_login(self.customer)

        response = self.client.patch(
            reverse("products:customer-cart-item-detail", args=[self.variant.id]),
            {"quantity": 4},
            content_type="application/json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()["items"][0]["quantity"], 4)
        self.assertEqual(response.json()["items"][0]["unit_price"], "175.00")
        self.assertEqual(
            CustomerCartItem.objects.get(
                customer=self.customer, variant=self.variant
            ).quantity,
            4,
        )

    def test_quantity_change_cannot_exceed_live_stock(self):
        CustomerCartItem.objects.create(
            customer=self.customer,
            variant=self.variant,
            quantity=1,
        )
        self.inventory.quantity_on_hand = 3
        self.inventory.save(update_fields=["quantity_on_hand", "updated_at"])
        self.client.force_login(self.customer)

        response = self.client.patch(
            reverse("products:customer-cart-item-detail", args=[self.variant.id]),
            {"quantity": 5},
            content_type="application/json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()["items"][0]["quantity"], 3)
        self.assertEqual(
            response.json()["adjustments"][0]["code"], "quantity_reduced"
        )

    def test_customer_cannot_change_another_customers_cart_line(self):
        other_customer = User.objects.create_user(
            email="quantity-other@example.com",
            phone_number="+233241000093",
            full_name="Quantity Other Customer",
            password="CustomerPass123!",
        )
        CustomerCartItem.objects.create(
            customer=other_customer,
            variant=self.variant,
            quantity=1,
        )
        self.client.force_login(self.customer)

        response = self.client.patch(
            reverse("products:customer-cart-item-detail", args=[self.variant.id]),
            {"quantity": 2},
            content_type="application/json",
        )

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_removing_cart_item_requires_authentication(self):
        response = self.client.delete(
            reverse("products:customer-cart-item-detail", args=[self.variant.id])
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_customer_can_remove_cart_item_and_receive_remaining_cart(self):
        second_variant = ProductVariant.objects.create(
            product=self.variant.product,
            name="Large",
            sku="CUSTOMER-CART-CREAM-LARGE",
            selling_price="250.00",
            cost_price="120.00",
        )
        BranchInventory.objects.create(
            branch=self.branch,
            product_variant=second_variant,
            quantity_on_hand=4,
        )
        CustomerCartItem.objects.bulk_create(
            [
                CustomerCartItem(
                    customer=self.customer,
                    variant=self.variant,
                    quantity=1,
                ),
                CustomerCartItem(
                    customer=self.customer,
                    variant=second_variant,
                    quantity=2,
                ),
            ]
        )
        self.client.force_login(self.customer)

        response = self.client.delete(
            reverse("products:customer-cart-item-detail", args=[self.variant.id])
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()["items"]), 1)
        self.assertEqual(
            response.json()["items"][0]["variant_id"], str(second_variant.id)
        )
        self.assertFalse(
            CustomerCartItem.objects.filter(
                customer=self.customer, variant=self.variant
            ).exists()
        )

    def test_customer_cannot_remove_another_customers_cart_line(self):
        other_customer = User.objects.create_user(
            email="remove-other@example.com",
            phone_number="+233241000094",
            full_name="Remove Other Customer",
            password="CustomerPass123!",
        )
        CustomerCartItem.objects.create(
            customer=other_customer,
            variant=self.variant,
            quantity=1,
        )
        self.client.force_login(self.customer)

        response = self.client.delete(
            reverse("products:customer-cart-item-detail", args=[self.variant.id])
        )

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertTrue(
            CustomerCartItem.objects.filter(
                customer=other_customer, variant=self.variant
            ).exists()
        )

    def test_customer_can_get_current_server_cart(self):
        CustomerCartItem.objects.create(
            customer=self.customer,
            variant=self.variant,
            quantity=2,
        )
        self.client.force_login(self.customer)

        response = self.client.get(reverse("products:customer-cart"))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()[0]["quantity"], 2)
        self.assertEqual(response.json()[0]["unit_price"], "175.00")

    def test_current_cart_is_scoped_to_the_signed_in_customer(self):
        other_customer = User.objects.create_user(
            email="other-cart@example.com",
            phone_number="+233241000092",
            full_name="Other Cart Customer",
            password="CustomerPass123!",
        )
        CustomerCartItem.objects.create(
            customer=other_customer,
            variant=self.variant,
            quantity=3,
        )
        self.client.force_login(self.customer)

        response = self.client.get(reverse("products:customer-cart"))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json(), [])

    def test_validated_cart_change_replaces_customer_cart(self):
        CustomerCartItem.objects.create(
            customer=self.customer,
            variant=self.variant,
            quantity=4,
        )
        self.client.force_login(self.customer)

        response = self.client.post(
            reverse("products:cart-validate"),
            {
                "items": [
                    {"variant_id": str(self.variant.id), "quantity": 2}
                ]
            },
            content_type="application/json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()["items"][0]["quantity"], 2)
        self.assertEqual(
            CustomerCartItem.objects.get(
                customer=self.customer, variant=self.variant
            ).quantity,
            2,
        )

    def test_cart_change_rechecks_current_price_and_stock(self):
        self.client.force_login(self.customer)
        response = self.client.post(
            reverse("products:cart-validate"),
            {
                "items": [
                    {"variant_id": str(self.variant.id), "quantity": 9}
                ]
            },
            content_type="application/json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()["items"][0]["quantity"], 5)
        self.assertEqual(response.json()["items"][0]["unit_price"], "175.00")
        self.assertEqual(
            response.json()["adjustments"][0]["code"], "quantity_reduced"
        )

    def test_out_of_stock_item_is_removed_during_cart_change(self):
        self.inventory.quantity_on_hand = 0
        self.inventory.save(update_fields=["quantity_on_hand", "updated_at"])
        self.client.force_login(self.customer)

        response = self.client.post(
            reverse("products:cart-validate"),
            {
                "items": [
                    {"variant_id": str(self.variant.id), "quantity": 1}
                ]
            },
            content_type="application/json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()["items"], [])
        self.assertEqual(response.json()["adjustments"][0]["code"], "out_of_stock")


class ManagementProductListApiTests(TestCase):
    def setUp(self):
        self.branch = Branch.objects.create(
            name="Makola management stock",
            code="MAKOLA-MANAGEMENT-STOCK",
            address="Accra",
            telephone_number="+233241370429",
            opening_days=["monday"],
            opening_time="07:30",
            closing_time="17:00",
        )
        category = ProductCategory.objects.create(
            name="Management products",
            slug="management-products",
        )
        self.product = Product.objects.create(
            category=category,
            name="Management Face Cream",
            slug="management-face-cream",
            description="Management stock test.",
            is_active=True,
            is_published=False,
        )
        variant = ProductVariant.objects.create(
            product=self.product,
            name="Standard",
            sku="MANAGEMENT-CREAM",
            selling_price="180.00",
            cost_price="100.00",
        )
        BranchInventory.objects.create(
            branch=self.branch,
            product_variant=variant,
            quantity_on_hand=8,
            quantity_reserved=2,
            reorder_level=6,
        )
        self.owner = User.objects.create_superuser(
            email="product-owner@example.com",
            phone_number="+233241000073",
            full_name="Product Owner",
            password="OwnerPass123!",
        )

    def test_owner_sees_drafts_and_complete_stock_summary(self):
        self.client.force_login(self.owner)

        response = self.client.get(reverse("products:management-list"))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()), 1)
        product = response.json()[0]
        self.assertEqual(product["publication_state"], "draft")
        self.assertEqual(product["minimum_price"], "180.00")
        self.assertEqual(product["active_variant_count"], 1)
        self.assertEqual(product["total_on_hand"], 8)
        self.assertEqual(product["total_reserved"], 2)
        self.assertEqual(product["total_available"], 6)
        self.assertEqual(product["low_stock_count"], 1)
        self.assertEqual(
            product["branch_stock"][0]["branch_code"],
            self.branch.code,
        )

    def test_customer_cannot_view_management_product_list(self):
        customer = User.objects.create_user(
            email="product-list-customer@example.com",
            phone_number="+233241000074",
            full_name="Product List Customer",
            password="CustomerPass123!",
        )
        self.client.force_login(customer)

        response = self.client.get(reverse("products:management-list"))

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_owner_can_create_product_variant_and_opening_branch_stock(self):
        self.client.force_login(self.owner)
        png = base64.b64decode(
            "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk+A8AAQUBAScY42YAAAAASUVORK5CYII="
        )
        category = self.product.category

        response = self.client.post(
            reverse("products:management-list"),
            {
                "name": "New Management Serum",
                "brand": "Golden Touch",
                "category_id": str(category.id),
                "description": "A new customer serum.",
                "image": SimpleUploadedFile(
                    "product.png",
                    png,
                    content_type="image/png",
                ),
                "publication_state": "draft",
                "is_featured": "true",
                "initial_variant_name": "Standard",
                "initial_sku": "new-serum-std",
                "initial_selling_price": "200.00",
                "initial_cost_price": "110.00",
                "initial_is_preorder": "false",
                "branch_stocks": json.dumps(
                    [
                        {
                            "branch_id": str(self.branch.id),
                            "quantity_on_hand": 12,
                            "reorder_level": 4,
                            "is_available": True,
                        }
                    ]
                ),
            },
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        product = Product.objects.get(name="New Management Serum")
        variant = product.variants.get()
        stock = variant.branch_inventory.get(branch=self.branch)
        self.assertEqual(product.slug, "new-management-serum")
        self.assertFalse(product.is_published)
        self.assertEqual(variant.sku, "NEW-SERUM-STD")
        self.assertEqual(stock.quantity_on_hand, 12)
        self.assertTrue(
            AuditLog.objects.filter(
                action="product.created",
                record_id=str(product.id),
                actor=self.owner,
            ).exists()
        )
        product.image.delete(save=False)

    def test_contact_for_price_product_does_not_require_prices(self):
        self.client.force_login(self.owner)
        png = base64.b64decode(
            "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk+A8AAQUBAScY42YAAAAASUVORK5CYII="
        )

        response = self.client.post(
            reverse("products:management-list"),
            {
                "name": "Price On Request Product",
                "category_id": str(self.product.category_id),
                "description": "Management confirms the current price on WhatsApp.",
                "price_type": "contact",
                "image": SimpleUploadedFile("contact.png", png, content_type="image/png"),
                "publication_state": "published",
                "is_featured": "false",
                "initial_variant_name": "Standard",
                "initial_sku": "contact-price-standard",
                "initial_is_preorder": "false",
                "branch_stocks": json.dumps(
                    [{
                        "branch_id": str(self.branch.id),
                        "quantity_on_hand": 1,
                        "reorder_level": 0,
                        "is_available": True,
                    }]
                ),
            },
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.json())
        product = Product.objects.get(name="Price On Request Product")
        variant = product.variants.get()
        self.assertEqual(variant.selling_price, 0)
        self.assertEqual(variant.cost_price, 0)
        product.image.delete(save=False)

    def test_owner_can_edit_product_variants_prices_and_branch_stock(self):
        self.client.force_login(self.owner)
        variant = self.product.variants.get()

        response = self.client.patch(
            reverse("products:management-detail", args=[self.product.id]),
            {
                "name": "Updated Management Face Cream",
                "brand": "Marcelito",
                "category_id": str(self.product.category_id),
                "description": "Updated management description.",
                "is_featured": "true",
                "publication_state": "published",
                "variants": json.dumps(
                    [
                        {
                            "id": str(variant.id),
                            "name": "Standard",
                            "sku": "management-cream-updated",
                            "selling_price": "195.00",
                            "cost_price": "105.00",
                            "is_preorder": False,
                            "estimated_availability_date": None,
                            "is_active": True,
                            "stocks": [
                                {
                                    "branch_id": str(self.branch.id),
                                    "quantity_on_hand": 10,
                                    "reorder_level": 3,
                                    "is_available": True,
                                }
                            ],
                        },
                        {
                            "name": "Large",
                            "sku": "management-cream-large",
                            "selling_price": "260.00",
                            "cost_price": "140.00",
                            "is_preorder": True,
                            "estimated_availability_date": "2099-12-31",
                            "is_active": True,
                            "stocks": [
                                {
                                    "branch_id": str(self.branch.id),
                                    "quantity_on_hand": 0,
                                    "reorder_level": 4,
                                    "is_available": True,
                                }
                            ],
                        },
                    ]
                ),
            },
            content_type="application/json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK, response.json())
        self.product.refresh_from_db()
        variant.refresh_from_db()
        self.assertEqual(self.product.name, "Updated Management Face Cream")
        self.assertTrue(self.product.is_published)
        self.assertEqual(variant.sku, "MANAGEMENT-CREAM-UPDATED")
        self.assertEqual(variant.selling_price, 195)
        self.assertEqual(
            variant.branch_inventory.get(branch=self.branch).quantity_on_hand, 10
        )
        self.assertTrue(
            self.product.variants.filter(
                name="Large", sku="MANAGEMENT-CREAM-LARGE"
            ).exists()
        )
        self.assertTrue(
            AuditLog.objects.filter(
                action="product.updated",
                record_id=str(self.product.id),
                actor=self.owner,
            ).exists()
        )

    def test_owner_can_change_product_to_contact_price_without_variant_prices(self):
        self.client.force_login(self.owner)
        variant = self.product.variants.get()

        response = self.client.patch(
            reverse("products:management-detail", args=[self.product.id]),
            {
                "name": self.product.name,
                "brand": self.product.brand,
                "category_id": str(self.product.category_id),
                "description": self.product.description,
                "price_type": "contact",
                "is_featured": "false",
                "publication_state": "published",
                "variants": json.dumps(
                    [{
                        "id": str(variant.id),
                        "name": variant.name,
                        "sku": variant.sku,
                        "is_preorder": False,
                        "estimated_availability_date": None,
                        "is_active": True,
                        "stocks": [{
                            "branch_id": str(self.branch.id),
                            "quantity_on_hand": 8,
                            "reorder_level": 6,
                            "is_available": True,
                        }],
                    }]
                ),
            },
            content_type="application/json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK, response.json())
        variant.refresh_from_db()
        self.assertEqual(variant.selling_price, 0)
        self.assertEqual(variant.cost_price, 0)

    def test_product_stock_cannot_be_reduced_below_reserved_quantity(self):
        self.client.force_login(self.owner)
        variant = self.product.variants.get()

        response = self.client.patch(
            reverse("products:management-detail", args=[self.product.id]),
            {
                "name": self.product.name,
                "brand": self.product.brand,
                "category_id": str(self.product.category_id),
                "description": self.product.description,
                "is_featured": "false",
                "publication_state": "draft",
                "variants": json.dumps(
                    [
                        {
                            "id": str(variant.id),
                            "name": variant.name,
                            "sku": variant.sku,
                            "selling_price": str(variant.selling_price),
                            "cost_price": str(variant.cost_price),
                            "is_preorder": False,
                            "estimated_availability_date": None,
                            "is_active": True,
                            "stocks": [
                                {
                                    "branch_id": str(self.branch.id),
                                    "quantity_on_hand": 1,
                                    "reorder_level": 3,
                                    "is_available": True,
                                }
                            ],
                        }
                    ]
                ),
            },
            content_type="application/json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            variant.branch_inventory.get(branch=self.branch).quantity_on_hand, 8
        )


class ManagementProductCategoryApiTests(TestCase):
    def setUp(self):
        self.owner = User.objects.create_superuser(
            email="product-category-owner@example.com",
            phone_number="+233241000075",
            full_name="Product Category Owner",
            password="OwnerPass123!",
        )
        self.customer = User.objects.create_user(
            email="product-category-customer@example.com",
            phone_number="+233241000076",
            full_name="Product Category Customer",
            password="CustomerPass123!",
        )

    def test_owner_can_create_and_update_product_category(self):
        self.client.force_login(self.owner)
        create = self.client.post(
            reverse("products:management-product-category-list"),
            {
                "name": "Body Treatments",
                "description": "Products for body care.",
                "display_order": 4,
                "is_active": True,
            },
            content_type="application/json",
        )

        self.assertEqual(create.status_code, status.HTTP_201_CREATED)
        category_id = create.json()["id"]
        self.assertEqual(create.json()["slug"], "body-treatments")

        update = self.client.patch(
            reverse(
                "products:management-product-category-detail",
                args=[category_id],
            ),
            {"name": "Body Care", "is_active": False},
            content_type="application/json",
        )

        self.assertEqual(update.status_code, status.HTTP_200_OK)
        self.assertEqual(update.json()["name"], "Body Care")
        self.assertEqual(update.json()["slug"], "body-treatments")
        self.assertFalse(update.json()["is_active"])
        self.assertTrue(
            AuditLog.objects.filter(
                action="product_category.created", record_id=category_id
            ).exists()
        )
        self.assertTrue(
            AuditLog.objects.filter(
                action="product_category.updated", record_id=category_id
            ).exists()
        )

    def test_category_with_products_cannot_be_deleted(self):
        category = ProductCategory.objects.create(
            name="Protected products",
            slug="protected-products",
        )
        Product.objects.create(
            category=category,
            name="Protected product",
            slug="protected-product",
            description="Cannot lose its category.",
        )
        self.client.force_login(self.owner)

        response = self.client.delete(
            reverse(
                "products:management-product-category-detail",
                args=[category.id],
            )
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertTrue(ProductCategory.objects.filter(id=category.id).exists())

    def test_customer_cannot_manage_product_categories(self):
        self.client.force_login(self.customer)
        response = self.client.get(
            reverse("products:management-product-category-list")
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
