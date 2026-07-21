from datetime import timedelta
from io import StringIO

from django.core.management import call_command
from django.core.management.base import CommandError
from django.db import IntegrityError, transaction
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from rest_framework import permissions, serializers, status
from rest_framework.test import APIRequestFactory
from rest_framework.views import APIView

from .models import IdempotencyRecord
from .references import generate_reference


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
        response = self.client.get("/api/v1/not-a-real-endpoint/")

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.json()["error"]["code"], "not_found")
        self.assertEqual(response["Content-Type"], "application/json")

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
