from django.urls import path

from .views import (
    CsrfTokenView,
    EmailVerificationResendView,
    EmailVerificationConfirmView,
    LoginView,
    PasswordResetConfirmView,
    PasswordResetRequestView,
    RegisterView,
)


app_name = "accounts"

urlpatterns = [
    path("csrf/", CsrfTokenView.as_view(), name="csrf"),
    path("register/", RegisterView.as_view(), name="register"),
    path("login/", LoginView.as_view(), name="login"),
    path("password-reset/", PasswordResetRequestView.as_view(), name="password-reset"),
    path("password-reset/confirm/", PasswordResetConfirmView.as_view(), name="password-reset-confirm"),
    path("resend-verification/", EmailVerificationResendView.as_view(), name="resend-verification"),
    path("verify-email/", EmailVerificationConfirmView.as_view(), name="verify-email"),
]
