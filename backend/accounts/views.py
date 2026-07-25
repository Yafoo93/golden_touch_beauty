import logging
from urllib.parse import quote, unquote

from django.conf import settings
from django.contrib.auth import login, logout
from django.contrib.auth.tokens import default_token_generator
from django.core import signing
from django.core.mail import send_mail
from django.middleware.csrf import get_token
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from django.utils import timezone
from rest_framework.authentication import SessionAuthentication
from rest_framework import status
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView

from auditlog.services import actor_role_for, client_device, client_ip, record_event

from .models import User
from .serializers import (
    CurrentUserSerializer,
    EmailVerificationConfirmSerializer,
    EmailVerificationResendSerializer,
    LoginSerializer,
    PasswordResetConfirmSerializer,
    PasswordResetRequestSerializer,
    RegistrationSerializer,
)


logger = logging.getLogger("golden_touch.auth")
PASSWORD_RESET_RESPONSE = {
    "detail": "If an active account uses that email address, password-reset instructions have been sent."
}
EMAIL_VERIFICATION_RESPONSE = {
    "detail": "If an unverified active account uses that email address, a verification link has been sent."
}


def enforce_csrf(request):
    SessionAuthentication().enforce_csrf(request)


class CsrfTokenView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        get_token(request)
        return Response({"detail": "CSRF cookie set."})


class CurrentUserView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response({"user": CurrentUserSerializer(request.user).data})


class RegisterView(APIView):
    permission_classes = [AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "auth-register"

    def post(self, request):
        enforce_csrf(request)
        serializer = RegistrationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        login(request, user, backend="accounts.backends.EmailOrPhoneBackend")
        get_token(request)
        record_event(
            action="auth.registered",
            record_type="user",
            record_id=user.pk,
            actor=user,
            actor_role=actor_role_for(user),
            new_values={
                "full_name": user.full_name,
                "email": user.email,
                "phone_number": user.phone_number,
            },
            ip_address=client_ip(request),
            device_identifier=client_device(request),
        )
        return Response(
            {"user": CurrentUserSerializer(user).data},
            status=status.HTTP_201_CREATED,
        )


class LoginView(APIView):
    permission_classes = [AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "auth-login"

    def post(self, request):
        enforce_csrf(request)
        serializer = LoginSerializer(data=request.data, context={"request": request})
        try:
            serializer.is_valid(raise_exception=True)
        except ValidationError:
            record_event(
                action="auth.login_failed",
                record_type="user",
                record_id=str(request.data.get("identifier", ""))[:255],
                ip_address=client_ip(request),
                device_identifier=client_device(request),
            )
            raise
        user = serializer.validated_data["user"]
        login(request, user, backend="accounts.backends.EmailOrPhoneBackend")
        get_token(request)
        record_event(
            action="auth.login_succeeded",
            record_type="user",
            record_id=user.pk,
            actor=user,
            actor_role=actor_role_for(user),
            ip_address=client_ip(request),
            device_identifier=client_device(request),
        )
        return Response({"user": CurrentUserSerializer(user).data})


class LogoutView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        enforce_csrf(request)
        user = request.user if request.user.is_authenticated else None
        logout(request)
        if user is not None:
            record_event(
                action="auth.logout",
                record_type="user",
                record_id=user.pk,
                actor=user,
                actor_role=actor_role_for(user),
                ip_address=client_ip(request),
                device_identifier=client_device(request),
            )
        return Response({"detail": "You have been signed out successfully."})


class PasswordResetRequestView(APIView):
    permission_classes = [AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "auth-reset"

    def post(self, request):
        enforce_csrf(request)
        serializer = PasswordResetRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = User.objects.filter(
            email__iexact=serializer.validated_data["email"],
            is_active=True,
        ).first()

        if user is not None:
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            token = default_token_generator.make_token(user)
            reset_url = f"{settings.FRONTEND_URL.rstrip('/')}/reset-password/{uid}.{token}"
            try:
                send_mail(
                    subject="Reset your Golden Touch password",
                    message=(
                        f"Hello {user.full_name},\n\n"
                        "We received a request to reset your Golden Touch password. "
                        f"Use this one-time link:\n\n{reset_url}\n\n"
                        "If you did not request this, you can ignore this email."
                    ),
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[user.email],
                    fail_silently=False,
                )
            except Exception:
                logger.exception(
                    "password_reset_email_failed",
                    extra={"user_id": str(user.pk)},
                )
            else:
                record_event(
                    action="auth.password_reset_requested",
                    record_type="user",
                    record_id=user.pk,
                    actor=user,
                    actor_role=actor_role_for(user),
                    ip_address=client_ip(request),
                    device_identifier=client_device(request),
                )

        return Response(PASSWORD_RESET_RESPONSE)


class PasswordResetConfirmView(APIView):
    permission_classes = [AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "auth-reset"

    def post(self, request):
        enforce_csrf(request)
        packed_token = str(request.data.get("token", "")).strip()
        try:
            uid, token = packed_token.rsplit(".", 1)
            user_id = force_str(urlsafe_base64_decode(uid))
            user = User.objects.get(pk=user_id, is_active=True)
        except (ValueError, TypeError, OverflowError, User.DoesNotExist):
            raise ValidationError(
                {"token": ["This password-reset link is invalid or has expired."]}
            )

        if not default_token_generator.check_token(user, token):
            raise ValidationError(
                {"token": ["This password-reset link is invalid or has expired."]}
            )

        serializer = PasswordResetConfirmSerializer(
            data=request.data,
            context={"user": user},
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        record_event(
            action="auth.password_reset_completed",
            record_type="user",
            record_id=user.pk,
            actor=user,
            actor_role=actor_role_for(user),
            ip_address=client_ip(request),
            device_identifier=client_device(request),
        )
        return Response({"detail": "Your password has been reset successfully."})


class EmailVerificationResendView(APIView):
    permission_classes = [AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "auth-verify"

    def post(self, request):
        enforce_csrf(request)
        serializer = EmailVerificationResendSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = User.objects.filter(
            email__iexact=serializer.validated_data["email"],
            is_active=True,
            email_verified_at__isnull=True,
        ).first()

        if user is not None:
            token = signing.dumps(
                {"user_id": str(user.pk), "email": user.email},
                salt="accounts.email-verification",
                compress=True,
            )
            verification_url = (
                f"{settings.FRONTEND_URL.rstrip('/')}/verify-email/"
                f"{quote(token, safe='')}"
            )
            try:
                send_mail(
                    subject="Verify your Golden Touch email address",
                    message=(
                        f"Hello {user.full_name},\n\n"
                        "Verify your email address using this secure link:\n\n"
                        f"{verification_url}\n\n"
                        "If you did not create this account, you can ignore this email."
                    ),
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[user.email],
                    fail_silently=False,
                )
            except Exception:
                logger.exception(
                    "email_verification_delivery_failed",
                    extra={"user_id": str(user.pk)},
                )
            else:
                record_event(
                    action="auth.email_verification_requested",
                    record_type="user",
                    record_id=user.pk,
                    actor=user,
                    actor_role=actor_role_for(user),
                    ip_address=client_ip(request),
                    device_identifier=client_device(request),
                )

        return Response(EMAIL_VERIFICATION_RESPONSE)


class EmailVerificationConfirmView(APIView):
    permission_classes = [AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "auth-verify"

    def post(self, request):
        enforce_csrf(request)
        serializer = EmailVerificationConfirmSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            payload = signing.loads(
                unquote(serializer.validated_data["token"]),
                salt="accounts.email-verification",
                max_age=settings.EMAIL_VERIFICATION_MAX_AGE_SECONDS,
            )
            user = User.objects.get(
                pk=payload["user_id"],
                email__iexact=payload["email"],
                is_active=True,
            )
        except (
            signing.BadSignature,
            signing.SignatureExpired,
            KeyError,
            TypeError,
            ValueError,
            User.DoesNotExist,
        ) as exc:
            raise ValidationError(
                {"token": ["This email-verification link is invalid or has expired."]}
            ) from exc

        if user.email_verified_at is None:
            user.email_verified_at = timezone.now()
            user.save(update_fields=["email_verified_at", "updated_at"])
            record_event(
                action="auth.email_verified",
                record_type="user",
                record_id=user.pk,
                actor=user,
                actor_role=actor_role_for(user),
                ip_address=client_ip(request),
                device_identifier=client_device(request),
            )

        return Response(
            {
                "detail": "Your email address has been verified successfully.",
                "email": user.email,
            }
        )
