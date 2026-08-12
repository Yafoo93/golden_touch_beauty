from copy import deepcopy
from unittest.mock import patch

from django.conf import settings
from django.core.cache import cache
from django.test import TestCase, override_settings
from django.urls import reverse
from rest_framework.throttling import ScopedRateThrottle

from accounts.models import User
from accounts.views import (
    EmailVerificationConfirmView,
    EmailVerificationResendView,
    LoginView,
    PasswordResetConfirmView,
    PasswordResetRequestView,
    RegisterView,
)
from bookings.views import CustomerBookingListCreateView
from orders.views import CheckoutCreateView
from pos.views import POSSaleCorrectionView, POSSaleHistoryView

from .throttling import UnsafeMethodScopedRateThrottle


TEST_REST_FRAMEWORK = deepcopy(settings.REST_FRAMEWORK)
TEST_REST_FRAMEWORK["DEFAULT_THROTTLE_RATES"] = {
    **TEST_REST_FRAMEWORK["DEFAULT_THROTTLE_RATES"],
    "auth-register": "2/minute",
    "auth-login": "2/minute",
    "auth-verify": "2/minute",
    "auth-reset": "2/minute",
    "payment-customer": "2/minute",
    "payment-pos": "2/minute",
}


@override_settings(REST_FRAMEWORK=TEST_REST_FRAMEWORK)
class AuthenticationAndPaymentRateLimitTests(TestCase):
    def setUp(self):
        cache.clear()
        self.rate_patch = patch.object(
            ScopedRateThrottle,
            "THROTTLE_RATES",
            TEST_REST_FRAMEWORK["DEFAULT_THROTTLE_RATES"],
        )
        self.rate_patch.start()

    def tearDown(self):
        self.rate_patch.stop()
        cache.clear()

    def test_every_sensitive_authentication_view_has_a_reviewed_scope(self):
        expected = {
            RegisterView: "auth-register",
            LoginView: "auth-login",
            PasswordResetRequestView: "auth-reset",
            PasswordResetConfirmView: "auth-reset",
            EmailVerificationResendView: "auth-verify",
            EmailVerificationConfirmView: "auth-verify",
        }
        for view_class, scope in expected.items():
            with self.subTest(view=view_class.__name__):
                self.assertIn(ScopedRateThrottle, view_class.throttle_classes)
                self.assertEqual(view_class.throttle_scope, scope)

    def test_repeated_login_attempts_are_rate_limited_by_client_address(self):
        for attempt in range(1, 4):
            response = self.client.post(
                reverse("accounts:login"),
                {"identifier": "missing@example.com", "password": "WrongPass123!"},
                content_type="application/json",
                REMOTE_ADDR="203.0.113.10",
            )
            if attempt <= 2:
                self.assertNotEqual(response.status_code, 429)
            else:
                self.assertEqual(response.status_code, 429)
                self.assertEqual(response.json()["error"]["code"], "rate_limited")

        independent = self.client.post(
            reverse("accounts:login"),
            {"identifier": "missing@example.com", "password": "WrongPass123!"},
            content_type="application/json",
            REMOTE_ADDR="203.0.113.11",
        )
        self.assertNotEqual(independent.status_code, 429)

    def test_every_money_creating_or_correcting_view_has_a_payment_scope(self):
        expected = {
            CustomerBookingListCreateView: "payment-customer",
            CheckoutCreateView: "payment-customer",
            POSSaleHistoryView: "payment-pos",
            POSSaleCorrectionView: "payment-pos",
        }
        for view_class, scope in expected.items():
            with self.subTest(view=view_class.__name__):
                self.assertIn(
                    UnsafeMethodScopedRateThrottle,
                    view_class.throttle_classes,
                )
                self.assertEqual(view_class.throttle_scope, scope)

    def test_customer_payment_limit_is_shared_and_does_not_limit_reads(self):
        customer = User.objects.create_user(
            email="rate-customer@example.com",
            phone_number="+233241370488",
            full_name="Rate Limit Customer",
            password="CustomerPass123!",
        )
        self.client.force_login(customer)

        for _ in range(5):
            self.assertNotEqual(
                self.client.get(reverse("bookings:customer-list")).status_code,
                429,
            )

        first = self.client.post(
            reverse("bookings:customer-list"), {}, content_type="application/json"
        )
        second = self.client.post(
            reverse("orders:checkout-create"), {}, content_type="application/json"
        )
        blocked = self.client.post(
            reverse("bookings:customer-list"), {}, content_type="application/json"
        )

        self.assertNotEqual(first.status_code, 429)
        self.assertNotEqual(second.status_code, 429)
        self.assertEqual(blocked.status_code, 429)
        self.assertEqual(blocked.json()["error"]["code"], "rate_limited")

        other_customer = User.objects.create_user(
            email="other-rate-customer@example.com",
            phone_number="+233241370487",
            full_name="Other Rate Limit Customer",
            password="CustomerPass123!",
        )
        self.client.force_login(other_customer)
        independent = self.client.post(
            reverse("orders:checkout-create"), {}, content_type="application/json"
        )
        self.assertNotEqual(independent.status_code, 429)
