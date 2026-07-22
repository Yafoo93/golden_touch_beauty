from django.contrib.auth import get_user_model
from django.conf import settings
from django.contrib.auth.tokens import default_token_generator
from django.core import signing
from django.core import mail
from django.test import TestCase
from django.urls import reverse
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from django.utils import timezone
from rest_framework import status
from urllib.parse import unquote, urlparse

from branches.models import Branch, BranchStaffAssignment
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

    def test_registration_requires_csrf_when_checks_are_enabled(self):
        from django.test import Client

        client = Client(enforce_csrf_checks=True)
        denied = client.post(
            reverse("accounts:register"),
            self.payload(),
            content_type="application/json",
        )
        self.assertEqual(denied.status_code, status.HTTP_403_FORBIDDEN)
        self.assertFalse(User.objects.filter(email="ama@example.com").exists())

        csrf_response = client.get(reverse("accounts:csrf"))
        token = csrf_response.cookies["csrftoken"].value
        allowed = client.post(
            reverse("accounts:register"),
            self.payload(),
            content_type="application/json",
            HTTP_X_CSRFTOKEN=token,
        )
        self.assertEqual(allowed.status_code, status.HTTP_201_CREATED)

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
        anonymous_session = self.client.session
        anonymous_session["pre_login_marker"] = True
        anonymous_session.save()
        anonymous_session_key = anonymous_session.session_key
        response = self.client.post(
            reverse("accounts:login"),
            {"identifier": "CUSTOMER@example.com", "password": "SafeCustomerPass!2026"},
            content_type="application/json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()["user"]["email"], "customer@example.com")
        self.assertEqual(str(self.client.session.get("_auth_user_id")), str(self.user.pk))
        self.assertTrue(response.cookies.get("csrftoken"))
        session_cookie = response.cookies[settings.SESSION_COOKIE_NAME]
        self.assertTrue(session_cookie["httponly"])
        self.assertEqual(session_cookie["samesite"], "Lax")
        self.assertEqual(session_cookie["path"], "/")
        self.assertNotEqual(self.client.session.session_key, anonymous_session_key)

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

    def test_customer_receives_account_destination(self):
        response = self.client.post(
            reverse("accounts:login"),
            {"identifier": self.user.email, "password": "SafeCustomerPass!2026"},
            content_type="application/json",
        )
        self.assertEqual(response.json()["user"]["post_login_path"], "/account")
        self.assertEqual(response.json()["user"]["portal_access"], [])

    def test_staff_destination_uses_active_branch_roles(self):
        branch = Branch.objects.create(
            name="Login Routing Branch",
            code="LOGIN_ROUTE",
            address="Accra",
            telephone_number="+233200000099",
            opening_days=["Monday"],
            opening_time="07:30",
            closing_time="19:00",
        )
        cashier = User.objects.create_user(
            email="routing-cashier@example.com",
            phone_number="+233241234573",
            full_name="Routing Cashier",
            password="SafeCustomerPass!2026",
            is_staff=True,
        )
        manager = User.objects.create_user(
            email="routing-manager@example.com",
            phone_number="+233241234574",
            full_name="Routing Manager",
            password="SafeCustomerPass!2026",
            is_staff=True,
        )
        BranchStaffAssignment.objects.create(
            branch=branch,
            staff=cashier,
            roles=[BranchStaffAssignment.Role.CASHIER],
        )
        BranchStaffAssignment.objects.create(
            branch=branch,
            staff=manager,
            roles=[BranchStaffAssignment.Role.MANAGER],
        )

        cashier_response = self.client.post(
            reverse("accounts:login"),
            {"identifier": cashier.email, "password": "SafeCustomerPass!2026"},
            content_type="application/json",
        )
        manager_response = self.client.post(
            reverse("accounts:login"),
            {"identifier": manager.email, "password": "SafeCustomerPass!2026"},
            content_type="application/json",
        )
        self.assertEqual(cashier_response.json()["user"]["post_login_path"], "/pos")
        self.assertEqual(cashier_response.json()["user"]["portal_access"], ["pos"])
        self.assertEqual(manager_response.json()["user"]["post_login_path"], "/management")
        self.assertEqual(manager_response.json()["user"]["portal_access"], ["management", "pos"])

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


class LogoutApiTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="logout@example.com",
            phone_number="+233241234572",
            full_name="Logout Customer",
            password="SafeCustomerPass!2026",
        )

    def test_logout_invalidates_authenticated_session(self):
        self.client.force_login(self.user, backend="accounts.backends.EmailOrPhoneBackend")
        self.assertIn("_auth_user_id", self.client.session)
        response = self.client.post(reverse("accounts:logout"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertNotIn("_auth_user_id", self.client.session)
        self.assertEqual(response.cookies[settings.SESSION_COOKIE_NAME].value, "")

    def test_logout_is_idempotent_for_anonymous_visitors(self):
        response = self.client.post(reverse("accounts:logout"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_logout_requires_csrf_when_checks_are_enabled(self):
        from django.test import Client

        client = Client(enforce_csrf_checks=True)
        client.force_login(self.user, backend="accounts.backends.EmailOrPhoneBackend")
        denied = client.post(reverse("accounts:logout"))
        self.assertEqual(denied.status_code, status.HTTP_403_FORBIDDEN)
        self.assertIn("_auth_user_id", client.session)
        csrf_response = client.get(reverse("accounts:csrf"))
        token = csrf_response.cookies["csrftoken"].value
        allowed = client.post(reverse("accounts:logout"), HTTP_X_CSRFTOKEN=token)
        self.assertEqual(allowed.status_code, status.HTTP_200_OK)
        self.assertNotIn("_auth_user_id", client.session)


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


class EmailVerificationResendApiTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="verify@example.com",
            phone_number="+233241234570",
            full_name="Verification Customer",
            password="SafeCustomerPass!2026",
        )

    def test_unverified_active_account_receives_verification_link(self):
        response = self.client.post(
            reverse("accounts:resend-verification"),
            {"email": "VERIFY@example.com"},
            content_type="application/json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, ["verify@example.com"])
        self.assertIn("/verify-email/", mail.outbox[0].body)
        verification_url = next(
            line for line in mail.outbox[0].body.splitlines() if "/verify-email/" in line
        )
        encoded_token = urlparse(verification_url).path.rsplit("/", 1)[-1]
        self.assertNotIn(":", encoded_token)
        payload = signing.loads(
            unquote(encoded_token),
            salt="accounts.email-verification",
        )
        self.assertEqual(payload["user_id"], str(self.user.pk))

    def test_unknown_and_verified_accounts_receive_same_response(self):
        unknown = self.client.post(
            reverse("accounts:resend-verification"),
            {"email": "unknown@example.com"},
            content_type="application/json",
        )
        self.user.email_verified_at = timezone.now()
        self.user.save(update_fields=["email_verified_at"])
        verified = self.client.post(
            reverse("accounts:resend-verification"),
            {"email": self.user.email},
            content_type="application/json",
        )
        self.assertEqual(unknown.status_code, status.HTTP_200_OK)
        self.assertEqual(unknown.json(), verified.json())
        self.assertEqual(mail.outbox, [])


class EmailVerificationConfirmApiTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="verification-confirm@example.com",
            phone_number="+233241234571",
            full_name="Verification Confirmation Customer",
            password="SafeCustomerPass!2026",
        )

    def token(self, **overrides):
        payload = {"user_id": str(self.user.pk), "email": self.user.email}
        payload.update(overrides)
        return signing.dumps(
            payload,
            salt="accounts.email-verification",
            compress=True,
        )

    def test_valid_link_verifies_account_and_is_idempotent(self):
        payload = {"token": self.token()}
        response = self.client.post(
            reverse("accounts:verify-email"),
            payload,
            content_type="application/json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertIsNotNone(self.user.email_verified_at)
        verified_at = self.user.email_verified_at

        repeated = self.client.post(
            reverse("accounts:verify-email"),
            payload,
            content_type="application/json",
        )
        self.assertEqual(repeated.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertEqual(self.user.email_verified_at, verified_at)

    def test_tampered_or_wrong_account_token_is_rejected(self):
        tampered = self.client.post(
            reverse("accounts:verify-email"),
            {"token": f"{self.token()}tampered"},
            content_type="application/json",
        )
        wrong_email = self.client.post(
            reverse("accounts:verify-email"),
            {"token": self.token(email="different@example.com")},
            content_type="application/json",
        )
        self.assertEqual(tampered.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(wrong_email.status_code, status.HTTP_400_BAD_REQUEST)
        self.user.refresh_from_db()
        self.assertIsNone(self.user.email_verified_at)
