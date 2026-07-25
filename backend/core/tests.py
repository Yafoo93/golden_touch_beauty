import json
import logging
import base64
from datetime import timedelta
from io import StringIO

from django.core.management import call_command
from django.core.management.base import CommandError
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import IntegrityError, transaction
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from rest_framework import permissions, serializers, status
from rest_framework.test import APIRequestFactory
from rest_framework.views import APIView

from .models import GalleryItem, IdempotencyRecord, Testimonial, WebsiteContent
from .references import generate_reference
from .logging import JsonFormatter


User = get_user_model()


class WebsiteContentApiTests(TestCase):
    def setUp(self):
        self.content = WebsiteContent.objects.create(
            key="test-home-title",
            page="home",
            section="Hero",
            label="Test title",
            value="Original title",
        )
        self.owner = User.objects.create_superuser(
            email="owner-content@example.com",
            phone_number="+233241000001",
            full_name="Content Owner",
            password="OwnerPass123!",
        )
        self.customer = User.objects.create_user(
            email="customer-content@example.com",
            phone_number="+233241000002",
            full_name="Content Customer",
            password="CustomerPass123!",
        )

    def test_public_list_only_contains_published_content(self):
        hidden = WebsiteContent.objects.create(
            key="test-hidden-title",
            page="home",
            section="Hero",
            label="Hidden title",
            value="Hidden",
            is_published=False,
        )
        response = self.client.get(reverse("core:public-content"))
        keys = {item["key"] for item in response.json()}

        self.assertEqual(response.status_code, 200)
        self.assertIn(self.content.key, keys)
        self.assertNotIn(hidden.key, keys)

    def test_owner_can_list_and_update_approved_content(self):
        self.client.force_login(self.owner)
        list_response = self.client.get(reverse("core:management-content-list"))
        update_response = self.client.patch(
            reverse("core:management-content-detail", args=[self.content.id]),
            data=json.dumps({"value": "Updated title", "key": "changed-key"}),
            content_type="application/json",
        )
        self.content.refresh_from_db()

        self.assertEqual(list_response.status_code, 200)
        self.assertEqual(update_response.status_code, 200)
        self.assertEqual(self.content.value, "Updated title")
        self.assertEqual(self.content.key, "test-home-title")
        self.assertEqual(self.content.updated_by, self.owner)

    def test_customer_cannot_manage_content(self):
        self.client.force_login(self.customer)
        response = self.client.patch(
            reverse("core:management-content-detail", args=[self.content.id]),
            data=json.dumps({"value": "Unauthorized update"}),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 403)


class GalleryItemApiTests(TestCase):
    def setUp(self):
        self.item = GalleryItem.objects.create(
            title="Published work",
            category="Skin",
            alt_text="A completed skin-care service",
            image_path="/images/facial_treatment.jpeg",
            display_order=1,
            is_published=True,
        )
        self.hidden = GalleryItem.objects.create(
            title="Draft work",
            category="Hair",
            alt_text="A draft hair-care image",
            image_path="/images/hair_treatment.jpeg",
            display_order=2,
            is_published=False,
        )
        self.owner = User.objects.create_superuser(
            email="gallery-owner@example.com",
            phone_number="+233241000011",
            full_name="Gallery Owner",
            password="OwnerPass123!",
        )
        self.customer = User.objects.create_user(
            email="gallery-customer@example.com",
            phone_number="+233241000012",
            full_name="Gallery Customer",
            password="CustomerPass123!",
        )

    def test_public_gallery_only_contains_published_items(self):
        response = self.client.get(reverse("core:public-gallery"))
        titles = {item["title"] for item in response.json()}

        self.assertEqual(response.status_code, 200)
        self.assertIn(self.item.title, titles)
        self.assertNotIn(self.hidden.title, titles)

    def test_owner_can_create_and_update_gallery_item(self):
        self.client.force_login(self.owner)
        png = base64.b64decode(
            "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk+A8AAQUBAScY42YAAAAASUVORK5CYII="
        )
        create_response = self.client.post(
            reverse("core:management-gallery-list"),
            {
                "title": "New gallery work",
                "category": "Bridal",
                "alt_text": "A completed bridal styling service",
                "display_size": "wide",
                "display_order": 3,
                "is_published": "true",
                "image": SimpleUploadedFile("gallery.png", png, content_type="image/png"),
            },
        )
        self.assertEqual(create_response.status_code, 201)

        update_response = self.client.patch(
            reverse("core:management-gallery-detail", args=[self.item.id]),
            data=json.dumps({"title": "Updated published work"}),
            content_type="application/json",
        )
        self.item.refresh_from_db()
        self.assertEqual(update_response.status_code, 200)
        self.assertEqual(self.item.title, "Updated published work")
        self.assertEqual(self.item.updated_by, self.owner)

    def test_customer_cannot_manage_gallery(self):
        self.client.force_login(self.customer)
        response = self.client.get(reverse("core:management-gallery-list"))
        self.assertEqual(response.status_code, 403)


class TestimonialModerationApiTests(TestCase):
    def setUp(self):
        self.pending = Testimonial.objects.create(
            client_name="Pending Client",
            service_context="Facial treatment",
            quote="A pending testimonial.",
        )
        self.public = Testimonial.objects.create(
            client_name="Approved Client",
            service_context="Hair care",
            quote="An approved and visible testimonial.",
            consent_confirmed=True,
            moderation_status=Testimonial.ModerationStatus.APPROVED,
            is_visible=True,
        )
        self.hidden = Testimonial.objects.create(
            client_name="Hidden Client",
            service_context="Bridal styling",
            quote="An approved but hidden testimonial.",
            consent_confirmed=True,
            moderation_status=Testimonial.ModerationStatus.APPROVED,
            is_visible=False,
        )
        self.owner = User.objects.create_superuser(
            email="testimonial-owner@example.com",
            phone_number="+233241000021",
            full_name="Testimonial Owner",
            password="OwnerPass123!",
        )
        self.customer = User.objects.create_user(
            email="testimonial-customer@example.com",
            phone_number="+233241000022",
            full_name="Testimonial Customer",
            password="CustomerPass123!",
        )

    def test_public_list_only_contains_approved_visible_consented_items(self):
        response = self.client.get(reverse("core:public-testimonials"))
        names = {item["client_name"] for item in response.json()}

        self.assertEqual(response.status_code, 200)
        self.assertIn(self.public.client_name, names)
        self.assertNotIn(self.pending.client_name, names)
        self.assertNotIn(self.hidden.client_name, names)

    def test_approval_requires_consent(self):
        self.client.force_login(self.owner)
        response = self.client.patch(
            reverse("core:management-testimonial-detail", args=[self.pending.id]),
            data=json.dumps({"moderation_status": "approved"}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 400)

    def test_owner_can_approve_and_show_testimonial(self):
        self.client.force_login(self.owner)
        response = self.client.patch(
            reverse("core:management-testimonial-detail", args=[self.pending.id]),
            data=json.dumps(
                {
                    "consent_confirmed": True,
                    "moderation_status": "approved",
                    "is_visible": True,
                    "is_featured": True,
                    "display_order": 1,
                }
            ),
            content_type="application/json",
        )
        self.pending.refresh_from_db()

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            self.pending.moderation_status,
            Testimonial.ModerationStatus.APPROVED,
        )
        self.assertTrue(self.pending.is_visible)
        self.assertEqual(self.pending.reviewed_by, self.owner)
        self.assertIsNotNone(self.pending.reviewed_at)

    def test_customer_cannot_moderate_testimonials(self):
        self.client.force_login(self.customer)
        response = self.client.get(reverse("core:management-testimonial-list"))
        self.assertEqual(response.status_code, 403)


class ValidationFailureView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        raise serializers.ValidationError({"email": ["This field is required."]})


class AuthenticationRequiredView(APIView):
    def get(self, request):
        raise AssertionError("The permission check should stop this view.")


class UnexpectedFailureView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        raise RuntimeError("Sensitive internal failure text")


class HealthCheckTests(TestCase):
    def test_health_check_does_not_expose_debug_configuration(self):
        response = self.client.get(reverse("core:health-check"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "ok")
        self.assertNotIn("debug", response.json())

    def test_request_has_correlation_header(self):
        response = self.client.get(
            reverse("core:health-check"),
            HTTP_X_REQUEST_ID="local-test-123",
        )

        self.assertEqual(response["X-Request-ID"], "local-test-123")

    def test_unsafe_correlation_header_is_replaced(self):
        response = self.client.get(
            reverse("core:health-check"),
            HTTP_X_REQUEST_ID="unsafe request id",
        )

        self.assertNotEqual(response["X-Request-ID"], "unsafe request id")


class ApiErrorResponseTests(TestCase):
    def setUp(self):
        self.factory = APIRequestFactory()

    def test_validation_errors_use_standard_envelope(self):
        request = self.factory.post("/test/", {}, format="json")
        response = ValidationFailureView.as_view()(request)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["error"]["code"], "validation_error")
        self.assertEqual(response.data["error"]["status"], 400)
        self.assertEqual(
            response.data["error"]["details"]["email"],
            ["This field is required."],
        )

    def test_authentication_errors_use_standard_envelope(self):
        request = self.factory.get("/test/")
        response = AuthenticationRequiredView.as_view()(request)

        self.assertIn(response.status_code, (401, 403))
        self.assertEqual(response.data["error"]["code"], "not_authenticated")

    def test_unknown_api_route_returns_json_error(self):
        response = self.client.get(
            "/api/v1/not-a-real-endpoint/",
            HTTP_X_REQUEST_ID="missing-route-123",
        )

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.json()["error"]["code"], "not_found")
        self.assertEqual(response["Content-Type"], "application/json")
        self.assertEqual(
            response.json()["error"]["request_id"],
            "missing-route-123",
        )

    def test_method_not_allowed_uses_standard_envelope(self):
        response = self.client.post(reverse("core:health-check"))

        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
        self.assertEqual(response.json()["error"]["code"], "method_not_allowed")

    def test_unexpected_errors_hide_internal_details(self):
        request = self.factory.get("/test/")
        with self.assertLogs("core.exceptions", level="ERROR"):
            response = UnexpectedFailureView.as_view()(request)

        self.assertEqual(
            response.status_code,
            status.HTTP_500_INTERNAL_SERVER_ERROR,
        )
        self.assertEqual(response.data["error"]["code"], "server_error")
        self.assertNotIn("Sensitive internal failure text", str(response.data))


class ClientErrorReportingTests(TestCase):
    def test_valid_client_error_is_accepted_and_logged(self):
        with self.assertLogs("golden_touch.health", level="ERROR") as logs:
            response = self.client.post(
                reverse("core:client-error-report"),
                {
                    "name": "RenderError",
                    "message": "Test browser render failure",
                    "digest": "digest-123",
                    "path": "/services",
                },
                content_type="application/json",
            )

        self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED)
        self.assertIn("client_error_reported", logs.output[0])

    def test_client_error_requires_a_message(self):
        response = self.client.post(
            reverse("core:client-error-report"),
            {"name": "RenderError"},
            content_type="application/json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.json()["error"]["code"], "validation_error")

    def test_anonymous_unsafe_api_request_requires_csrf(self):
        from django.test import Client

        client = Client(enforce_csrf_checks=True)
        payload = {
            "name": "RenderError",
            "message": "CSRF boundary test",
            "path": "/services",
        }
        denied = client.post(
            reverse("core:client-error-report"),
            payload,
            content_type="application/json",
        )
        self.assertEqual(denied.status_code, status.HTTP_403_FORBIDDEN)

        csrf_response = client.get(reverse("accounts:csrf"))
        token = csrf_response.cookies["csrftoken"].value
        with self.assertLogs("golden_touch.health", level="ERROR"):
            allowed = client.post(
                reverse("core:client-error-report"),
                payload,
                content_type="application/json",
                HTTP_X_CSRFTOKEN=token,
            )
        self.assertEqual(allowed.status_code, status.HTTP_202_ACCEPTED)


class JsonLoggingTests(TestCase):
    def test_formatter_outputs_machine_readable_context(self):
        record = logging.LogRecord(
            "golden_touch.test",
            logging.INFO,
            __file__,
            1,
            "request_completed",
            (),
            None,
        )
        record.request_id = "format-test-123"
        record.status_code = 200

        payload = json.loads(JsonFormatter().format(record))

        self.assertEqual(payload["message"], "request_completed")
        self.assertEqual(payload["request_id"], "format-test-123")
        self.assertEqual(payload["status_code"], 200)


class ReferenceTests(TestCase):
    def test_generated_reference_has_prefix_and_no_spaces(self):
        reference = generate_reference("ord")

        self.assertTrue(reference.startswith("ORD-"))
        self.assertNotIn(" ", reference)


class IdempotencyRecordTests(TestCase):
    def test_scope_and_key_are_unique_together(self):
        values = {
            "scope": "payment.create",
            "key": "request-123",
            "request_hash": "a" * 64,
            "expires_at": timezone.now() + timedelta(hours=24),
        }
        IdempotencyRecord.objects.create(**values)

        with self.assertRaises(IntegrityError), transaction.atomic():
            IdempotencyRecord.objects.create(**values)


class DevelopmentSeedCommandTests(TestCase):
    def test_seed_command_creates_expected_records_and_is_idempotent(self):
        from branches.models import Branch
        from inventory.models import BranchInventory
        from products.models import Product, ProductCategory, ProductVariant
        from services.models import (
            Service,
            ServiceBranchAvailability,
            ServiceCategory,
        )

        output = StringIO()
        call_command("seed_development_data", force=True, stdout=output)

        self.assertEqual(Branch.objects.count(), 2)
        self.assertEqual(ServiceCategory.objects.count(), 4)
        self.assertEqual(Service.objects.count(), 13)
        self.assertEqual(ServiceBranchAvailability.objects.count(), 26)
        self.assertEqual(ProductCategory.objects.count(), 6)
        self.assertEqual(Product.objects.count(), 10)
        self.assertEqual(ProductVariant.objects.count(), 10)
        self.assertEqual(BranchInventory.objects.count(), 20)
        self.assertEqual(
            set(Branch.objects.values_list("code", flat=True)),
            {"MAKOLA", "TSE_ADDO"},
        )
        self.assertIn("Development seed complete", output.getvalue())

        makola_inventory = BranchInventory.objects.filter(
            branch__code="MAKOLA"
        ).first()
        makola_inventory.quantity_on_hand = 7
        makola_inventory.save(update_fields=["quantity_on_hand"])

        call_command("seed_development_data", force=True, stdout=StringIO())

        self.assertEqual(Branch.objects.count(), 2)
        self.assertEqual(Service.objects.count(), 13)
        self.assertEqual(Product.objects.count(), 10)
        makola_inventory.refresh_from_db()
        self.assertEqual(makola_inventory.quantity_on_hand, 7)

    def test_seed_command_is_blocked_outside_debug_without_force(self):
        with self.assertRaises(CommandError):
            call_command("seed_development_data", stdout=StringIO())

# Create your tests here.
