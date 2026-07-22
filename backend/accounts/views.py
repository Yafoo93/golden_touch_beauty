import logging

from django.conf import settings
from django.contrib.auth import login
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail
from django.middleware.csrf import get_token
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from rest_framework.authentication import SessionAuthentication
from rest_framework import status
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import User
from .serializers import (
    CurrentUserSerializer,
    LoginSerializer,
    PasswordResetConfirmSerializer,
    PasswordResetRequestSerializer,
    RegistrationSerializer,
)


logger = logging.getLogger("golden_touch.auth")
PASSWORD_RESET_RESPONSE = {
    "detail": "If an active account uses that email address, password-reset instructions have been sent."
}


def enforce_csrf(request):
    SessionAuthentication().enforce_csrf(request)


class CsrfTokenView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        get_token(request)
        return Response({"detail": "CSRF cookie set."})


class RegisterView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        enforce_csrf(request)
        serializer = RegistrationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        login(request, user, backend="accounts.backends.EmailOrPhoneBackend")
        get_token(request)
        return Response(
            {"user": CurrentUserSerializer(user).data},
            status=status.HTTP_201_CREATED,
        )


class LoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        enforce_csrf(request)
        serializer = LoginSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data["user"]
        login(request, user, backend="accounts.backends.EmailOrPhoneBackend")
        get_token(request)
        return Response({"user": CurrentUserSerializer(user).data})


class PasswordResetRequestView(APIView):
    permission_classes = [AllowAny]

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

        return Response(PASSWORD_RESET_RESPONSE)


class PasswordResetConfirmView(APIView):
    permission_classes = [AllowAny]

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
        return Response({"detail": "Your password has been reset successfully."})
