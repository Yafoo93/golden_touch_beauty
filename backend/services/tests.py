import base64
import json

from django.test import TestCase
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from rest_framework import status

from branches.models import Branch
from auditlog.models import AuditLog

from .models import Service, ServiceBranchAvailability, ServiceCategory


User = get_user_model()


class FeaturedServiceApiTests(TestCase):
    def test_only_published_active_featured_services_are_returned(self):
        branch = Branch.objects.create(
            name="Makola",
            code="MAKOLA",
            address="Accra",
            telephone_number="024 137 0429",
            opening_days=["monday"],
            opening_time="07:30",
            closing_time="17:00",
        )
        category = ServiceCategory.objects.create(name="Skin", slug="skin")
        service = Service.objects.create(
            category=category,
            name="Facial",
            slug="facial",
            short_description="A facial treatment.",
            description="A facial treatment.",
            price="250.00",
            duration_minutes=60,
            image_path="/images/facial_treatment.jpeg",
            is_featured=True,
            is_active=True,
            is_published=True,
        )
        ServiceBranchAvailability.objects.create(service=service, branch=branch)
        Service.objects.create(
            category=category,
            name="Hidden",
            slug="hidden",
            short_description="Not featured.",
            description="Not featured.",
            price="100.00",
            duration_minutes=60,
            is_featured=False,
            is_active=True,
            is_published=True,
        )

        response = self.client.get(reverse("services:featured"))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()), 1)
        self.assertEqual(response.json()[0]["slug"], "facial")
        self.assertEqual(response.json()[0]["available_at"], ["Makola"])


class PublicServiceCatalogueApiTests(TestCase):
    def setUp(self):
        self.branch = Branch.objects.create(
            name="Makola",
            code="MAKOLA-CATALOGUE",
            address="Accra",
            telephone_number="+233241370429",
            opening_days=["monday"],
            opening_time="07:30",
            closing_time="17:00",
        )
        self.skin = ServiceCategory.objects.create(
            name="Skin catalogue",
            slug="skin-catalogue",
            display_order=1,
        )
        self.hair = ServiceCategory.objects.create(
            name="Hair catalogue",
            slug="hair-catalogue",
            display_order=2,
        )
        self.facial = self._service(
            category=self.skin,
            name="Brightening Facial",
            slug="brightening-facial",
            description="A radiance-focused facial treatment.",
        )
        self.hair_service = self._service(
            category=self.hair,
            name="Hair Hydration",
            slug="hair-hydration",
            description="A moisture-restoring hair service.",
        )
        ServiceBranchAvailability.objects.create(
            service=self.facial,
            branch=self.branch,
        )
        ServiceBranchAvailability.objects.create(
            service=self.hair_service,
            branch=self.branch,
        )
        hidden = self._service(
            category=self.skin,
            name="Hidden Treatment",
            slug="hidden-treatment",
            description="Not public.",
            is_published=False,
        )
        ServiceBranchAvailability.objects.create(service=hidden, branch=self.branch)
        self._service(
            category=self.skin,
            name="Unavailable Treatment",
            slug="unavailable-treatment",
            description="No active branch availability.",
        )

    def _service(
        self,
        *,
        category,
        name,
        slug,
        description,
        is_published=True,
    ):
        return Service.objects.create(
            category=category,
            name=name,
            slug=slug,
            short_description=description,
            description=description,
            price="250.00",
            duration_minutes=60,
            image_path="/images/facial_treatment.jpeg",
            is_active=True,
            is_published=is_published,
        )

    def test_list_only_returns_published_services_available_at_active_branch(self):
        response = self.client.get(reverse("services:list"))
        slugs = {service["slug"] for service in response.json()}

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(slugs, {"brightening-facial", "hair-hydration"})

    def test_list_filters_by_category(self):
        response = self.client.get(
            reverse("services:list"),
            {"category": self.skin.slug},
        )
        self.assertEqual(
            [service["slug"] for service in response.json()],
            ["brightening-facial"],
        )

    def test_list_filters_services_by_selected_branch_code(self):
        second_branch = Branch.objects.create(
            name="Tse Addo catalogue",
            code="TSE-ADDO-CATALOGUE",
            address="Accra",
            telephone_number="+233207911043",
            opening_days=["monday"],
            opening_time="07:30",
            closing_time="19:00",
        )
        ServiceBranchAvailability.objects.create(
            service=self.hair_service,
            branch=second_branch,
        )

        response = self.client.get(
            reverse("services:list"),
            {"branch": second_branch.code},
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            [service["slug"] for service in response.json()],
            ["hair-hydration"],
        )

    def test_list_searches_name_description_and_category(self):
        response = self.client.get(reverse("services:list"), {"search": "radiance"})
        self.assertEqual(
            [service["slug"] for service in response.json()],
            ["brightening-facial"],
        )

    def test_list_supports_safe_ordering(self):
        self.hair_service.price = "100.00"
        self.hair_service.save(update_fields=["price", "updated_at"])

        response = self.client.get(reverse("services:list"), {"ordering": "price"})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            [service["slug"] for service in response.json()],
            ["hair-hydration", "brightening-facial"],
        )

    def test_categories_only_include_categories_with_public_available_services(self):
        empty = ServiceCategory.objects.create(
            name="Empty catalogue",
            slug="empty-catalogue",
        )
        response = self.client.get(reverse("services:categories"))
        slugs = {category["slug"] for category in response.json()}

        self.assertIn(self.skin.slug, slugs)
        self.assertIn(self.hair.slug, slugs)
        self.assertNotIn(empty.slug, slugs)

    def test_detail_returns_full_service_and_available_branch(self):
        self.facial.maximum_price = "350.00"
        self.facial.price_type = Service.PriceType.RANGE
        self.facial.pricing_notes = "Final price depends on consultation."
        self.facial.save()

        response = self.client.get(
            reverse("services:detail", args=[self.facial.slug])
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()["description"], self.facial.description)
        self.assertEqual(response.json()["maximum_price"], "350.00")
        self.assertEqual(response.json()["price_type"], "range")
        self.assertEqual(
            response.json()["available_branches"][0]["name"],
            self.branch.name,
        )
        self.assertNotIn("is_active", response.json())
        self.assertNotIn("is_published", response.json())
        self.assertNotIn("created_at", response.json())

    def test_detail_hides_drafts_and_services_without_active_branch(self):
        hidden_response = self.client.get(
            reverse("services:detail", args=["hidden-treatment"])
        )
        unavailable_response = self.client.get(
            reverse("services:detail", args=["unavailable-treatment"])
        )

        self.assertEqual(hidden_response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(
            unavailable_response.status_code,
            status.HTTP_404_NOT_FOUND,
        )

    def test_owner_management_list_includes_drafts_and_unavailable_services(self):
        owner = User.objects.create_superuser(
            email="service-owner@example.com",
            phone_number="+233241000031",
            full_name="Service Owner",
            password="OwnerPass123!",
        )
        self.client.force_login(owner)

        response = self.client.get(reverse("services:management-list"))
        slugs = {service["slug"] for service in response.json()}

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("hidden-treatment", slugs)
        self.assertIn("unavailable-treatment", slugs)
        facial = next(
            service
            for service in response.json()
            if service["slug"] == self.facial.slug
        )
        self.assertEqual(
            facial["branch_availability"][0]["branch_code"],
            self.branch.code,
        )

    def test_customer_cannot_view_management_service_list(self):
        customer = User.objects.create_user(
            email="service-customer@example.com",
            phone_number="+233241000032",
            full_name="Service Customer",
            password="CustomerPass123!",
        )
        self.client.force_login(customer)

        response = self.client.get(reverse("services:management-list"))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_customer_cannot_create_or_update_services(self):
        customer = User.objects.create_user(
            email="service-write-customer@example.com",
            phone_number="+233241000039",
            full_name="Service Write Customer",
            password="CustomerPass123!",
        )
        self.client.force_login(customer)

        create_response = self.client.post(
            reverse("services:management-list"),
            data={},
        )
        update_response = self.client.patch(
            reverse("services:management-detail", args=[self.facial.id]),
            data=json.dumps({"pricing_notes": "Unauthorized change"}),
            content_type="application/json",
        )

        self.assertEqual(create_response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(update_response.status_code, status.HTTP_403_FORBIDDEN)

    def test_inactive_service_cannot_remain_published(self):
        self.facial.is_active = False
        self.facial.is_published = True
        self.facial.save()
        self.facial.refresh_from_db()

        self.assertFalse(self.facial.is_published)
        self.assertEqual(
            self.facial.publication_state,
            Service.PublicationState.INACTIVE,
        )

    def test_owner_can_create_service_with_image_and_branch_availability(self):
        owner = User.objects.create_superuser(
            email="service-create-owner@example.com",
            phone_number="+233241000033",
            full_name="Service Create Owner",
            password="OwnerPass123!",
        )
        self.client.force_login(owner)
        png = base64.b64decode(
            "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk+A8AAQUBAScY42YAAAAASUVORK5CYII="
        )
        response = self.client.post(
            reverse("services:management-list"),
            {
                "name": "New Clinical Service",
                "category_id": str(self.skin.id),
                "short_description": "A newly created clinical service.",
                "description": "Full information about the newly created service.",
                "price_type": "fixed",
                "price": "400.00",
                "pricing_notes": "",
                "duration_minutes": "90",
                "image": SimpleUploadedFile(
                    "service.png",
                    png,
                    content_type="image/png",
                ),
                "is_clinic_service": "true",
                "is_home_service": "false",
                "requires_full_payment": "true",
                "allows_pay_at_clinic": "true",
                "is_consultation": "false",
                "is_featured": "false",
                "publication_state": "draft",
                "branch_ids": [str(self.branch.id)],
            },
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        service = Service.objects.get(name="New Clinical Service")
        self.assertEqual(service.slug, "new-clinical-service")
        self.assertFalse(service.is_published)
        self.assertEqual(response.json()["publication_state"], "draft")
        self.assertTrue(
            AuditLog.objects.filter(
                action="service.created",
                record_id=str(service.id),
                actor=owner,
            ).exists()
        )
        self.assertTrue(
            ServiceBranchAvailability.objects.filter(
                service=service,
                branch=self.branch,
                is_available=True,
            ).exists()
        )
        service.image.delete(save=False)

    def test_owner_can_save_result_images_without_customer_email_for_testing(self):
        owner = User.objects.create_superuser(
            email="service-result-test-owner@example.com",
            phone_number="+233241000133",
            full_name="Service Result Test Owner",
            password="OwnerPass123!",
        )
        self.client.force_login(owner)
        png = base64.b64decode(
            "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk+A8AAQUBAScY42YAAAAASUVORK5CYII="
        )
        response = self.client.post(
            reverse("services:management-list"),
            {
                "name": "Unlinked Result Test Service",
                "category_id": str(self.skin.id),
                "short_description": "A private result-image test.",
                "description": "A result pair may be tested before a customer is linked.",
                "price_type": "starting_from",
                "price": "400.00",
                "duration_minutes": "90",
                "image": SimpleUploadedFile("service.png", png, content_type="image/png"),
                "before_image": SimpleUploadedFile("before.png", png, content_type="image/png"),
                "after_image": SimpleUploadedFile("after.png", png, content_type="image/png"),
                "is_clinic_service": "true",
                "requires_full_payment": "true",
                "allows_pay_at_clinic": "true",
                "result_images_approved": "false",
                "publication_state": "draft",
                "branch_ids": [str(self.branch.id)],
            },
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        service = Service.objects.get(name="Unlinked Result Test Service")
        self.assertIsNone(service.result_photo_customer)
        self.assertFalse(service.result_photo_consent_confirmed)
        self.assertFalse(service.result_images_approved)
        self.assertTrue(bool(service.before_image))
        self.assertTrue(bool(service.after_image))
        service.image.delete(save=False)
        service.before_image.delete(save=False)
        service.after_image.delete(save=False)

    def test_result_images_without_customer_cannot_be_approved_publicly(self):
        owner = User.objects.create_superuser(
            email="service-result-approval-owner@example.com",
            phone_number="+233241000134",
            full_name="Service Result Approval Owner",
            password="OwnerPass123!",
        )
        self.client.force_login(owner)
        png = base64.b64decode(
            "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk+A8AAQUBAScY42YAAAAASUVORK5CYII="
        )
        response = self.client.post(
            reverse("services:management-list"),
            {
                "name": "Unsafe Public Result Service",
                "category_id": str(self.skin.id),
                "short_description": "An invalid public result test.",
                "description": "Unlinked photographs must not be published.",
                "price_type": "starting_from",
                "price": "400.00",
                "duration_minutes": "90",
                "image": SimpleUploadedFile("service.png", png, content_type="image/png"),
                "before_image": SimpleUploadedFile("before.png", png, content_type="image/png"),
                "after_image": SimpleUploadedFile("after.png", png, content_type="image/png"),
                "is_clinic_service": "true",
                "requires_full_payment": "true",
                "allows_pay_at_clinic": "true",
                "result_images_approved": "true",
                "publication_state": "draft",
                "branch_ids": [str(self.branch.id)],
            },
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("result_images_approved", response.json()["error"]["details"])
        self.assertFalse(Service.objects.filter(name="Unsafe Public Result Service").exists())

    def test_create_rejects_range_without_maximum_price(self):
        owner = User.objects.create_superuser(
            email="service-validation-owner@example.com",
            phone_number="+233241000034",
            full_name="Service Validation Owner",
            password="OwnerPass123!",
        )
        self.client.force_login(owner)
        png = base64.b64decode(
            "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk+A8AAQUBAScY42YAAAAASUVORK5CYII="
        )
        response = self.client.post(
            reverse("services:management-list"),
            {
                "name": "Invalid Range Service",
                "category_id": str(self.skin.id),
                "short_description": "Invalid range example.",
                "description": "Invalid range example.",
                "price_type": "range",
                "price": "400.00",
                "duration_minutes": "60",
                "image": SimpleUploadedFile(
                    "invalid-service.png",
                    png,
                    content_type="image/png",
                ),
                "is_clinic_service": "true",
                "requires_full_payment": "true",
                "allows_pay_at_clinic": "true",
                "is_active": "true",
                "branch_ids": [str(self.branch.id)],
            },
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(Service.objects.filter(name="Invalid Range Service").exists())

    def test_owner_can_update_service_and_synchronize_branch_availability(self):
        second_branch = Branch.objects.create(
            name="Tse Addo catalogue",
            code="TSE-ADDO-CATALOGUE",
            address="Accra",
            telephone_number="+233207911043",
            opening_days=["monday"],
            opening_time="07:30",
            closing_time="19:00",
        )
        owner = User.objects.create_superuser(
            email="service-edit-owner@example.com",
            phone_number="+233241000035",
            full_name="Service Edit Owner",
            password="OwnerPass123!",
        )
        original_slug = self.facial.slug
        self.client.force_login(owner)
        response = self.client.patch(
            reverse("services:management-detail", args=[self.facial.id]),
            data=json.dumps({
                "name": "Renamed Brightening Facial",
                "category_id": str(self.skin.id),
                "short_description": self.facial.short_description,
                "description": self.facial.description,
                "price_type": "range",
                "price": "300.00",
                "maximum_price": "450.00",
                "pricing_notes": "Price depends on the treatment plan.",
                "duration_minutes": "120",
                "is_clinic_service": "true",
                "is_home_service": "false",
                "requires_full_payment": "true",
                "allows_pay_at_clinic": "false",
                "is_consultation": "false",
                "is_featured": "true",
                "publication_state": "published",
                "branch_ids": [str(second_branch.id)],
            }),
            content_type="application/json",
        )
        self.facial.refresh_from_db()

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()["publication_state"], "published")
        self.assertEqual(self.facial.name, "Renamed Brightening Facial")
        self.assertEqual(self.facial.slug, original_slug)
        self.assertEqual(self.facial.duration_minutes, 120)
        self.assertFalse(
            ServiceBranchAvailability.objects.get(
                service=self.facial,
                branch=self.branch,
            ).is_available
        )
        self.assertTrue(
            ServiceBranchAvailability.objects.get(
                service=self.facial,
                branch=second_branch,
            ).is_available
        )
        self.assertTrue(
            AuditLog.objects.filter(
                action="service.updated",
                record_id=str(self.facial.id),
                actor=owner,
            ).exists()
        )

    def test_owner_can_partially_update_without_resending_branch_assignments(self):
        owner = User.objects.create_superuser(
            email="service-partial-owner@example.com",
            phone_number="+233241000038",
            full_name="Service Partial Owner",
            password="OwnerPass123!",
        )
        self.client.force_login(owner)

        response = self.client.patch(
            reverse("services:management-detail", args=[self.facial.id]),
            data=json.dumps({"pricing_notes": "Updated independently."}),
            content_type="application/json",
        )
        self.facial.refresh_from_db()

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(self.facial.pricing_notes, "Updated independently.")
        self.assertTrue(
            self.facial.branch_availability.filter(
                branch=self.branch,
                is_available=True,
            ).exists()
        )

    def test_customer_cannot_view_management_service_detail(self):
        customer = User.objects.create_user(
            email="service-detail-customer@example.com",
            phone_number="+233241000036",
            full_name="Service Detail Customer",
            password="CustomerPass123!",
        )
        self.client.force_login(customer)
        response = self.client.get(
            reverse("services:management-detail", args=[self.facial.id])
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_owner_can_create_and_update_service_category_with_stable_slug(self):
        owner = User.objects.create_superuser(
            email="category-owner@example.com",
            phone_number="+233241000041",
            full_name="Category Owner",
            password="OwnerPass123!",
        )
        self.client.force_login(owner)
        create_response = self.client.post(
            reverse("services:management-category-list"),
            data=json.dumps(
                {
                    "name": "Body Treatments",
                    "description": "Full-body treatment services.",
                    "display_order": 4,
                    "is_active": True,
                }
            ),
            content_type="application/json",
        )
        self.assertEqual(create_response.status_code, status.HTTP_201_CREATED)
        category = ServiceCategory.objects.get(name="Body Treatments")
        original_slug = category.slug

        update_response = self.client.patch(
            reverse("services:management-category-detail", args=[category.id]),
            data=json.dumps(
                {
                    "name": "Body and Wellness",
                    "description": "Updated category description.",
                    "display_order": 5,
                    "is_active": False,
                }
            ),
            content_type="application/json",
        )
        category.refresh_from_db()
        self.assertEqual(update_response.status_code, status.HTTP_200_OK)
        self.assertEqual(category.slug, original_slug)
        self.assertFalse(category.is_active)

    def test_category_with_services_cannot_be_deleted(self):
        owner = User.objects.create_superuser(
            email="category-delete-owner@example.com",
            phone_number="+233241000042",
            full_name="Category Delete Owner",
            password="OwnerPass123!",
        )
        self.client.force_login(owner)
        response = self.client.delete(
            reverse("services:management-category-detail", args=[self.skin.id])
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertTrue(ServiceCategory.objects.filter(id=self.skin.id).exists())

    def test_empty_category_can_be_deleted(self):
        empty = ServiceCategory.objects.create(
            name="Temporary category",
            slug="temporary-category",
        )
        owner = User.objects.create_superuser(
            email="empty-category-owner@example.com",
            phone_number="+233241000043",
            full_name="Empty Category Owner",
            password="OwnerPass123!",
        )
        self.client.force_login(owner)
        response = self.client.delete(
            reverse("services:management-category-detail", args=[empty.id])
        )
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(ServiceCategory.objects.filter(id=empty.id).exists())

    def test_customer_cannot_manage_service_categories(self):
        customer = User.objects.create_user(
            email="category-customer@example.com",
            phone_number="+233241000044",
            full_name="Category Customer",
            password="CustomerPass123!",
        )
        self.client.force_login(customer)
        response = self.client.get(reverse("services:management-category-list"))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_option_based_service_requires_and_publishes_structured_options(self):
        owner = User.objects.create_superuser(
            email="price-option-owner@example.com",
            phone_number="+233241000045",
            full_name="Price Option Owner",
            password="OwnerPass123!",
        )
        self.client.force_login(owner)
        png = base64.b64decode(
            "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk+A8AAQUBAScY42YAAAAASUVORK5CYII="
        )
        options = [
            {
                "name": "Standard",
                "description": "Standard treatment option.",
                "price": "300.00",
                "duration_minutes": 60,
                "display_order": 1,
            },
            {
                "name": "Premium",
                "description": "Extended premium option.",
                "price": "500.00",
                "duration_minutes": 90,
                "display_order": 2,
            },
        ]
        response = self.client.post(
            reverse("services:management-list"),
            {
                "name": "Configurable Facial",
                "category_id": str(self.skin.id),
                "short_description": "Choose a treatment level.",
                "description": "A facial with structured price choices.",
                "price_type": "options",
                "price": "0.00",
                "duration_minutes": "60",
                "image": SimpleUploadedFile("options.png", png, content_type="image/png"),
                "is_clinic_service": "true",
                "requires_full_payment": "true",
                "allows_pay_at_clinic": "true",
                "is_active": "true",
                "is_published": "true",
                "branch_ids": [str(self.branch.id)],
                "price_options": json.dumps(options),
            },
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        service = Service.objects.get(name="Configurable Facial")
        self.assertEqual(service.price, 300)
        self.assertEqual(service.price_options.filter(is_active=True).count(), 2)

        detail = self.client.get(
            reverse("services:detail", args=[service.slug])
        )
        self.assertEqual(detail.status_code, status.HTTP_200_OK)
        self.assertEqual(
            [option["name"] for option in detail.json()["price_options"]],
            ["Standard", "Premium"],
        )
        service.image.delete(save=False)

    def test_option_based_service_without_options_is_rejected(self):
        owner = User.objects.create_superuser(
            email="missing-option-owner@example.com",
            phone_number="+233241000046",
            full_name="Missing Option Owner",
            password="OwnerPass123!",
        )
        self.client.force_login(owner)
        png = base64.b64decode(
            "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk+A8AAQUBAScY42YAAAAASUVORK5CYII="
        )
        response = self.client.post(
            reverse("services:management-list"),
            {
                "name": "Missing Options",
                "category_id": str(self.skin.id),
                "short_description": "Invalid option service.",
                "description": "Invalid option service.",
                "price_type": "options",
                "price": "0.00",
                "duration_minutes": "60",
                "image": SimpleUploadedFile("missing-options.png", png, content_type="image/png"),
                "is_clinic_service": "true",
                "requires_full_payment": "true",
                "allows_pay_at_clinic": "true",
                "is_active": "true",
                "branch_ids": [str(self.branch.id)],
                "price_options": "[]",
            },
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
