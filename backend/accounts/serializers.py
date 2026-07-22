import re

from django.contrib.auth import authenticate
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import transaction
from django.utils import timezone
from rest_framework import serializers

from customers.models import CustomerConsent


User = get_user_model()
CURRENT_TERMS_VERSION = "draft-2026-07"
CURRENT_PRIVACY_VERSION = "draft-2026-07"


class RegistrationSerializer(serializers.Serializer):
    full_name = serializers.CharField(max_length=200)
    email = serializers.EmailField(max_length=254)
    phone_number = serializers.CharField(max_length=20)
    password = serializers.CharField(write_only=True, trim_whitespace=False)
    confirm_password = serializers.CharField(write_only=True, trim_whitespace=False)
    terms_privacy_agreed = serializers.BooleanField(write_only=True)
    marketing_consent = serializers.BooleanField(default=False, required=False)

    def validate_full_name(self, value):
        normalized = " ".join(value.split())
        if len(normalized) < 2:
            raise serializers.ValidationError("Enter your full name.")
        return normalized

    def validate_email(self, value):
        normalized = User.objects.normalize_email(value).lower()
        if User.objects.filter(email__iexact=normalized).exists():
            raise serializers.ValidationError("An account with this email already exists.")
        return normalized

    def validate_phone_number(self, value):
        normalized = re.sub(r"[\s()-]", "", value)
        if normalized.startswith("0"):
            normalized = f"+233{normalized[1:]}"
        elif normalized.startswith("233"):
            normalized = f"+{normalized}"
        if not re.fullmatch(r"\+[1-9]\d{8,14}", normalized):
            raise serializers.ValidationError("Enter a valid phone number with its country code.")
        if User.objects.filter(phone_number=normalized).exists():
            raise serializers.ValidationError("An account with this phone number already exists.")
        return normalized

    def validate_terms_privacy_agreed(self, value):
        if value is not True:
            raise serializers.ValidationError("You must agree to the Terms and Privacy Policy.")
        return value

    def validate(self, attrs):
        if attrs["password"] != attrs["confirm_password"]:
            raise serializers.ValidationError({"confirm_password": "Passwords do not match."})
        candidate = User(
            full_name=attrs["full_name"],
            email=attrs["email"],
            phone_number=attrs["phone_number"],
        )
        try:
            validate_password(attrs["password"], user=candidate)
        except DjangoValidationError as exc:
            raise serializers.ValidationError({"password": list(exc.messages)}) from exc
        return attrs

    @transaction.atomic
    def create(self, validated_data):
        password = validated_data.pop("password")
        validated_data.pop("confirm_password")
        validated_data.pop("terms_privacy_agreed")
        marketing_consent = validated_data.pop("marketing_consent", False)
        user = User.objects.create_user(password=password, **validated_data)
        now = timezone.now()
        CustomerConsent.objects.create(
            user=user,
            terms_version=CURRENT_TERMS_VERSION,
            privacy_version=CURRENT_PRIVACY_VERSION,
            terms_privacy_accepted_at=now,
            marketing_consent=marketing_consent,
            marketing_consent_updated_at=now,
        )
        return user


class CurrentUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ("id", "full_name", "email", "phone_number", "is_staff", "is_superuser")
        read_only_fields = fields


class LoginSerializer(serializers.Serializer):
    identifier = serializers.CharField(max_length=254, trim_whitespace=True)
    password = serializers.CharField(write_only=True, trim_whitespace=False)

    default_error_messages = {
        "invalid_credentials": "The email/phone number or password is incorrect.",
    }

    def validate(self, attrs):
        identifier = attrs["identifier"].strip()
        if "@" not in identifier:
            identifier = re.sub(r"[\s()-]", "", identifier)
            if identifier.startswith("0"):
                identifier = f"+233{identifier[1:]}"
            elif identifier.startswith("233"):
                identifier = f"+{identifier}"

        user = authenticate(
            request=self.context.get("request"),
            username=identifier,
            password=attrs["password"],
        )
        if user is None:
            self.fail("invalid_credentials")
        attrs["user"] = user
        return attrs


class PasswordResetRequestSerializer(serializers.Serializer):
    email = serializers.EmailField(max_length=254)

    def validate_email(self, value):
        return User.objects.normalize_email(value).lower()


class PasswordResetConfirmSerializer(serializers.Serializer):
    token = serializers.CharField(write_only=True, trim_whitespace=True)
    password = serializers.CharField(write_only=True, trim_whitespace=False)
    confirm_password = serializers.CharField(write_only=True, trim_whitespace=False)

    def validate(self, attrs):
        if attrs["password"] != attrs["confirm_password"]:
            raise serializers.ValidationError({"confirm_password": "Passwords do not match."})

        user = self.context["user"]
        try:
            validate_password(attrs["password"], user=user)
        except DjangoValidationError as exc:
            raise serializers.ValidationError({"password": list(exc.messages)}) from exc
        attrs["user"] = user
        return attrs

    def save(self, **kwargs):
        user = self.validated_data["user"]
        user.set_password(self.validated_data["password"])
        user.save(update_fields=["password", "updated_at"])
        return user
