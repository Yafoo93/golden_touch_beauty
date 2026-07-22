from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import default_token_generator
from django.core import mail
from django.test import TestCase
from django.urls import reverse
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from rest_framework import status

from customers.models import CustomerConsent


User = get_user_model()


class RegistrationApiTests(TestCase):
    def payload(self, **overrides):
        data = {
            "full_name": "Ama Mensah",
            "email": "ama@example.com",
            "phone_number": "024 123 4567",
            "password": "SafeCustomerPass!2026",
            "confirm_password": "SafeCustomerPass!2026",
            "terms_privacy_agreed": True,
            "marketing_consent": False,
        }
        data.update(overrides)
        return data

    def test_registration_creates_customer_consent_and_session(self):
        response = self.client.post(
            reverse("accounts:register"),
            self.payload(marketing_consent=True),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        user = User.objects.get(email="ama@example.com")
        self.assertEqual(user.phone_number, "+233241234567")
        self.assertFalse(user.is_staff)
        self.assertTrue(user.check_password("SafeCustomerPass!2026"))
        self.assertNotEqual(user.password, "SafeCustomerPass!2026")
        self.assertEqual(str(self.client.session.get("_auth_user_id")), str(user.pk))
        self.assertTrue(user.customer_consent.marketing_consent)
        self.assertTrue(response.cookies.get("csrftoken"))

    def test_terms_and_privacy_agreement_is_required(self):
        response = self.client.post(
            reverse("accounts:register"),
            self.payload(terms_privacy_agreed=False),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(User.objects.filter(email="ama@example.com").exists())

    def test_password_confirmation_must_match(self):
        response = self.client.post(
            reverse("accounts:register"),
            self.payload(confirm_password="DifferentPass!2026"),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_duplicate_email_and_phone_are_rejected(self):
        User.objects.create_user(
            email="ama@example.com",
            phone_number="+233241234567",
            full_name="Existing Customer",
            password="SafeCustomerPass!2026",
        )
        response = self.client.post(
            reverse("accounts:register"),
            self.payload(),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(CustomerConsent.objects.count(), 0)


class LoginApiTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="customer@example.com",
            phone_number="+233241234567",
            full_name="Customer User",
            password="SafeCustomerPass!2026",
        )

    def test_login_with_email_creates_session_and_csrf_cookie(self):
        response = self.client.post(
            reverse("accounts:login"),
            {"identifier": "CUSTOMER@example.com", "password": "SafeCustomerPass!2026"},
            content_type="application/json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()["user"]["email"], "customer@example.com")
        self.assertEqual(str(self.client.session.get("_auth_user_id")), str(self.user.pk))
        self.assertTrue(response.cookies.get("csrftoken"))

    def test_login_with_local_ghana_phone_number(self):
        response = self.client.post(
            reverse("accounts:login"),
            {"identifier": "024 123 4567", "password": "SafeCustomerPass!2026"},
            content_type="application/json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_invalid_credentials_use_generic_error(self):
        response = self.client.post(
            reverse("accounts:login"),
            {"identifier": "unknown@example.com", "password": "WrongPassword"},
            content_type="application/json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("incorrect", str(response.json()).lower())

    def test_csrf_is_required_when_checks_are_enabled(self):
        from django.test import Client

        client = Client(enforce_csrf_checks=True)
        denied = client.post(
            reverse("accounts:login"),
            {"identifier": "customer@example.com", "password": "SafeCustomerPass!2026"},
            content_type="application/json",
        )
        self.assertEqual(denied.status_code, status.HTTP_403_FORBIDDEN)

        csrf_response = client.get(reverse("accounts:csrf"))
        token = csrf_response.cookies["csrftoken"].value
        allowed = client.post(
            reverse("accounts:login"),
            {"identifier": "customer@example.com", "password": "SafeCustomerPass!2026"},
            content_type="application/json",
            HTTP_X_CSRFTOKEN=token,
        )
        self.assertEqual(allowed.status_code, status.HTTP_200_OK)


class PasswordResetRequestApiTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="reset@example.com",
            phone_number="+233241234568",
            full_name="Reset Customer",
            password="SafeCustomerPass!2026",
        )

    def test_existing_account_receives_one_time_reset_link(self):
        response = self.client.post(
            reverse("accounts:password-reset"),
            {"email": "RESET@example.com"},
            content_type="application/json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, ["reset@example.com"])
        self.assertIn("/reset-password/", mail.outbox[0].body)
        self.assertNotIn(self.user.password, mail.outbox[0].body)

    def test_unknown_email_returns_identical_response_without_email(self):
        existing = self.client.post(
            reverse("accounts:password-reset"),
            {"email": "reset@example.com"},
            content_type="application/json",
        )
        mail.outbox.clear()
        unknown = self.client.post(
            reverse("accounts:password-reset"),
            {"email": "unknown@example.com"},
            content_type="application/json",
        )
        self.assertEqual(unknown.status_code, status.HTTP_200_OK)
        self.assertEqual(unknown.json(), existing.json())
        self.assertEqual(mail.outbox, [])

    def test_inactive_account_does_not_receive_email(self):
        self.user.is_active = False
        self.user.save(update_fields=["is_active"])
        response = self.client.post(
            reverse("accounts:password-reset"),
            {"email": "reset@example.com"},
            content_type="application/json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(mail.outbox, [])


class PasswordResetConfirmApiTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="confirm-reset@example.com",
            phone_number="+233241234569",
            full_name="Reset Confirmation Customer",
            password="OldSafePass!2026",
        )

    def token(self):
        uid = urlsafe_base64_encode(force_bytes(self.user.pk))
        return f"{uid}.{default_token_generator.make_token(self.user)}"

    def test_valid_token_sets_new_password_and_cannot_be_reused(self):
        packed_token = self.token()
        payload = {
            "token": packed_token,
            "password": "NewSafePass!2026",
            "confirm_password": "NewSafePass!2026",
        }
        response = self.client.post(
            reverse("accounts:password-reset-confirm"),
            payload,
            content_type="application/json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password("NewSafePass!2026"))

        reused = self.client.post(
            reverse("accounts:password-reset-confirm"),
            payload,
            content_type="application/json",
        )
        self.assertEqual(reused.status_code, status.HTTP_400_BAD_REQUEST)

    def test_invalid_token_is_rejected(self):
        response = self.client.post(
            reverse("accounts:password-reset-confirm"),
            {
                "token": "invalid-token",
                "password": "NewSafePass!2026",
                "confirm_password": "NewSafePass!2026",
            },
            content_type="application/json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_password_confirmation_and_strength_are_validated(self):
        response = self.client.post(
            reverse("accounts:password-reset-confirm"),
            {
                "token": self.token(),
                "password": "short",
                "confirm_password": "different",
            },
            content_type="application/json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password("OldSafePass!2026"))
