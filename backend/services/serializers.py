import json

from rest_framework import serializers
from django.db import transaction
from django.utils.text import slugify

from branches.serializers import PublicBranchSerializer
from branches.models import Branch
from accounts.models import User
from customers.models import CustomerConsent
from core.uploads import RestrictedImageField, validate_image_upload

from .models import (
    Service,
    ServiceBranchAvailability,
    ServiceCategory,
    ServicePriceOption,
)


class ServicePriceOptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = ServicePriceOption
        fields = (
            "id", "name", "description", "price", "duration_minutes",
            "display_order",
        )
        read_only_fields = fields


class ServicePriceOptionInputSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=150)
    description = serializers.CharField(max_length=300, required=False, allow_blank=True)
    price = serializers.DecimalField(max_digits=12, decimal_places=2, min_value=0)
    duration_minutes = serializers.IntegerField(min_value=1, max_value=1440, required=False, allow_null=True)
    display_order = serializers.IntegerField(min_value=0, max_value=32767, required=False)


class FeaturedServiceSerializer(serializers.ModelSerializer):
    category = serializers.CharField(source="category.name", read_only=True)
    available_at = serializers.SerializerMethodField()
    image_path = serializers.SerializerMethodField()
    has_result_images = serializers.SerializerMethodField()

    class Meta:
        model = Service
        fields = (
            "name",
            "slug",
            "category",
            "short_description",
            "price",
            "duration_minutes",
            "image_path",
            "has_result_images",
            "available_at",
        )

    def get_available_at(self, service):
        return [
            availability.branch.name
            for availability in service.branch_availability.all()
            if availability.is_available and availability.branch.is_active
        ]

    def get_image_path(self, service):
        if service.image:
            return service.image.url
        return service.image_path

    def get_has_result_images(self, service):
        customer_id = service.result_photo_customer_id
        consent_is_active = bool(
            customer_id
            and CustomerConsent.objects.filter(
                user_id=customer_id,
                photograph_consent=True,
            ).exists()
        )
        return bool(
            service.before_image
            and service.after_image
            and service.result_photo_consent_confirmed
            and service.result_images_approved
            and consent_is_active
        )


class PublicServiceSerializer(FeaturedServiceSerializer):
    category_slug = serializers.CharField(source="category.slug", read_only=True)
    price_options = serializers.SerializerMethodField()
    available_branches = serializers.SerializerMethodField()

    class Meta(FeaturedServiceSerializer.Meta):
        fields = ("id",) + FeaturedServiceSerializer.Meta.fields + (
            "category_slug",
            "price_type",
            "pricing_notes",
            "allows_pay_at_clinic",
            "price_options",
            "available_branches",
        )

    def get_price_options(self, service):
        options = [option for option in service.price_options.all() if option.is_active]
        return ServicePriceOptionSerializer(options, many=True).data

    def get_available_branches(self, service):
        branches = [
            availability.branch
            for availability in service.branch_availability.all()
            if availability.is_available and availability.branch.is_active
        ]
        return PublicBranchSerializer(branches, many=True).data


class PublicServiceCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = ServiceCategory
        fields = ("name", "slug")
        read_only_fields = fields


class PublicServiceDetailSerializer(PublicServiceSerializer):
    price_type_label = serializers.CharField(
        source="get_price_type_display",
        read_only=True,
    )
    before_image_url = serializers.SerializerMethodField()
    after_image_url = serializers.SerializerMethodField()

    class Meta(PublicServiceSerializer.Meta):
        fields = PublicServiceSerializer.Meta.fields + (
            "description",
            "maximum_price",
            "price_type_label",
            "is_clinic_service",
            "is_home_service",
            "requires_full_payment",
            "is_consultation",
            "before_image_url",
            "after_image_url",
        )

    def _approved_result_url(self, service, field):
        if not self.get_has_result_images(service):
            return None
        image = getattr(service, field)
        return image.url if image else None

    def get_before_image_url(self, service):
        return self._approved_result_url(service, "before_image")

    def get_after_image_url(self, service):
        return self._approved_result_url(service, "after_image")



class ManagementServiceListSerializer(serializers.ModelSerializer):
    category = serializers.CharField(source="category.name", read_only=True)
    branch_availability = serializers.SerializerMethodField()
    image_path = serializers.SerializerMethodField()
    publication_state = serializers.CharField(read_only=True)

    class Meta:
        model = Service
        fields = (
            "id", "name", "slug", "category", "price_type", "price",
            "maximum_price", "pricing_notes", "duration_minutes", "image_path",
            "is_featured", "is_active", "is_published", "publication_state",
            "requires_full_payment", "allows_pay_at_clinic",
            "branch_availability", "updated_at",
        )
        read_only_fields = fields

    def get_branch_availability(self, service):
        return [
            {
                "branch_id": str(availability.branch_id),
                "branch_code": availability.branch.code,
                "branch_name": availability.branch.name,
                "branch_is_active": availability.branch.is_active,
                "is_available": availability.is_available,
            }
            for availability in service.branch_availability.all()
        ]

    def get_image_path(self, service):
        if service.image:
            return service.image.url
        return service.image_path


class ManagementServiceCategoryOptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = ServiceCategory
        fields = ("id", "name")
        read_only_fields = fields


class ManagementServiceBranchOptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Branch
        fields = ("id", "code", "name")
        read_only_fields = fields


class ManagementServiceCreateSerializer(serializers.ModelSerializer):
    category_id = serializers.PrimaryKeyRelatedField(
        source="category",
        queryset=ServiceCategory.objects.filter(is_active=True),
    )
    branch_ids = serializers.PrimaryKeyRelatedField(
        source="branches_for_creation",
        queryset=Branch.objects.filter(is_active=True),
        many=True,
        allow_empty=False,
        write_only=True,
    )
    image = RestrictedImageField(write_only=True, required=False)
    before_image = RestrictedImageField(write_only=True, required=False)
    after_image = RestrictedImageField(write_only=True, required=False)
    result_photo_customer_email = serializers.EmailField(
        write_only=True, required=False, allow_blank=True
    )
    price_options = serializers.CharField(write_only=True, required=False, default="[]")
    publication_state = serializers.ChoiceField(
        choices=Service.PublicationState.choices,
        required=False,
    )

    class Meta:
        model = Service
        fields = (
            "id", "name", "category_id", "short_description", "description",
            "price_type", "price", "maximum_price", "pricing_notes",
            "duration_minutes", "image", "is_clinic_service",
            "before_image", "after_image", "result_photo_consent_confirmed",
            "result_photo_consent_reference", "result_images_approved",
            "result_photo_customer_email",
            "is_home_service", "requires_full_payment", "allows_pay_at_clinic",
            "is_consultation", "is_featured", "is_active", "is_published",
            "branch_ids",
            "price_options",
            "publication_state",
        )
        read_only_fields = (
            "id",
            "result_photo_consent_confirmed",
            "result_photo_consent_reference",
        )

    def validate_image(self, image):
        return validate_image_upload(image)

    def validate_before_image(self, image):
        return validate_image_upload(image)

    def validate_after_image(self, image):
        return validate_image_upload(image)

    def validate(self, attrs):
        publication_state = attrs.pop("publication_state", None)
        if publication_state is not None:
            attrs["is_active"] = publication_state != Service.PublicationState.INACTIVE
            attrs["is_published"] = publication_state == Service.PublicationState.PUBLISHED
        elif attrs.get("is_active") is False:
            attrs["is_published"] = False
        elif attrs.get("is_published") is True:
            attrs["is_active"] = True

        raw_options = attrs.pop("price_options", None)
        if raw_options is None and self.instance:
            option_data = [
                {
                    "name": option.name,
                    "description": option.description,
                    "price": option.price,
                    "duration_minutes": option.duration_minutes,
                    "display_order": option.display_order,
                }
                for option in self.instance.price_options.filter(is_active=True)
            ]
        else:
            try:
                option_data = json.loads(raw_options or "[]")
            except (TypeError, ValueError) as exc:
                raise serializers.ValidationError(
                    {"price_options": "Price options must be valid JSON."}
                ) from exc
        if not isinstance(option_data, list):
            raise serializers.ValidationError(
                {"price_options": "Price options must be a list."}
            )
        option_serializer = ServicePriceOptionInputSerializer(data=option_data, many=True)
        option_serializer.is_valid(raise_exception=True)
        normalized_options = option_serializer.validated_data
        names = [option["name"].strip().casefold() for option in normalized_options]
        if len(names) != len(set(names)):
            raise serializers.ValidationError(
                {"price_options": "Price option names must be unique."}
            )
        price_type = attrs.get(
            "price_type",
            self.instance.price_type if self.instance else Service.PriceType.STARTING_FROM,
        )
        price = attrs.get("price", self.instance.price if self.instance else None)
        maximum = attrs.get(
            "maximum_price",
            self.instance.maximum_price if self.instance else None,
        )
        pricing_notes = attrs.get(
            "pricing_notes",
            self.instance.pricing_notes if self.instance else "",
        ).strip()
        if price_type == Service.PriceType.RANGE:
            if maximum is None:
                raise serializers.ValidationError(
                    {"maximum_price": "A maximum price is required for a price range."}
                )
            if price is not None and maximum < price:
                raise serializers.ValidationError(
                    {"maximum_price": "Maximum price cannot be lower than the starting price."}
                )
        else:
            attrs["maximum_price"] = None
        if price_type == Service.PriceType.OPTIONS and not normalized_options:
            raise serializers.ValidationError(
                {"price_options": "Add at least one option for option-based pricing."}
            )
        if price_type != Service.PriceType.OPTIONS:
            normalized_options = []
        if price_type == Service.PriceType.QUOTATION and not pricing_notes:
            raise serializers.ValidationError(
                {"pricing_notes": "Explain the quotation process."}
            )
        if not attrs.get("is_clinic_service", True) and not attrs.get("is_home_service", False):
            raise serializers.ValidationError(
                {"is_clinic_service": "Select at least one service setting."}
            )
        if not attrs.get("image") and not (
            self.instance and (self.instance.image or self.instance.image_path)
        ):
            raise serializers.ValidationError({"image": "Upload a service image."})
        customer_email_supplied = "result_photo_customer_email" in attrs
        customer_email = attrs.pop("result_photo_customer_email", "").strip().lower()
        customer = getattr(self.instance, "result_photo_customer", None)
        if customer_email_supplied:
            customer = User.objects.filter(
                email__iexact=customer_email,
                is_active=True,
                is_staff=False,
            ).first() if customer_email else None
            if customer_email and customer is None:
                raise serializers.ValidationError(
                    {"result_photo_customer_email": "No active customer account uses this email address."}
                )
        before = attrs.get("before_image", getattr(self.instance, "before_image", None))
        after = attrs.get("after_image", getattr(self.instance, "after_image", None))
        consent_record = (
            CustomerConsent.objects.filter(user=customer).first()
            if customer else None
        )
        consent = bool(consent_record and consent_record.photograph_consent)
        approved = attrs.get(
            "result_images_approved",
            getattr(self.instance, "result_images_approved", False),
        )
        reference = (
            f"account-consent:{consent_record.id}:{consent_record.photograph_consent_updated_at.isoformat()}"
            if consent_record and consent_record.photograph_consent_updated_at
            else ""
        )
        if bool(before) != bool(after):
            raise serializers.ValidationError(
                {"before_image": "Upload both the before and after image as one result pair."}
            )
        if (before or after) and not customer:
            raise serializers.ValidationError(
                {"result_photo_customer_email": "Link the customer whose before-and-after images are being uploaded."}
            )
        if (before or after) and not consent:
            raise serializers.ValidationError(
                {"result_photo_customer_email": "This customer has not granted photograph advertising consent, or has withdrawn it."}
            )
        if approved and not (before and after):
            raise serializers.ValidationError(
                {"result_images_approved": "A complete consented image pair is required before approval."}
            )
        if approved and not consent:
            attrs["result_images_approved"] = False
        attrs["result_photo_customer"] = customer
        attrs["result_photo_consent_confirmed"] = consent
        attrs["result_photo_consent_reference"] = reference
        attrs["price_options_for_sync"] = normalized_options
        if price_type == Service.PriceType.OPTIONS:
            attrs["price"] = min(option["price"] for option in normalized_options)
        return attrs

    def _unique_slug(self, name):
        base = slugify(name) or "service"
        slug = base
        counter = 2
        while Service.objects.filter(slug=slug).exists():
            slug = f"{base}-{counter}"
            counter += 1
        return slug

    @transaction.atomic
    def create(self, validated_data):
        branches = validated_data.pop("branches_for_creation")
        price_options = validated_data.pop("price_options_for_sync")
        service = Service.objects.create(
            slug=self._unique_slug(validated_data["name"]),
            **validated_data,
        )
        ServiceBranchAvailability.objects.bulk_create(
            [
                ServiceBranchAvailability(
                    service=service,
                    branch=branch,
                    is_available=True,
                )
                for branch in branches
            ]
        )
        ServicePriceOption.objects.bulk_create(
            [
                ServicePriceOption(service=service, **option)
                for option in price_options
            ]
        )
        return service

    @transaction.atomic
    def update(self, instance, validated_data):
        branches = validated_data.pop("branches_for_creation", None)
        price_options = validated_data.pop("price_options_for_sync")
        for field, value in validated_data.items():
            setattr(instance, field, value)
        instance.save()

        if branches is not None:
            selected_ids = {branch.id for branch in branches}
            existing = {
                availability.branch_id: availability
                for availability in instance.branch_availability.all()
            }
            for branch in branches:
                availability = existing.get(branch.id)
                if availability is None:
                    ServiceBranchAvailability.objects.create(
                        service=instance,
                        branch=branch,
                        is_available=True,
                    )
                elif not availability.is_available:
                    availability.is_available = True
                    availability.save(update_fields=["is_available", "updated_at"])
            instance.branch_availability.exclude(branch_id__in=selected_ids).update(
                is_available=False
            )
        selected_names = set()
        for order, option in enumerate(price_options):
            name = option["name"].strip()
            selected_names.add(name)
            defaults = {
                **option,
                "name": name,
                "display_order": option.get("display_order", order),
                "is_active": True,
            }
            ServicePriceOption.objects.update_or_create(
                service=instance,
                name=name,
                defaults=defaults,
            )
        instance.price_options.exclude(name__in=selected_names).update(is_active=False)
        return instance


class ManagementServiceDetailSerializer(serializers.ModelSerializer):
    category_id = serializers.UUIDField(read_only=True)
    category_name = serializers.CharField(source="category.name", read_only=True)
    branch_ids = serializers.SerializerMethodField()
    image_path = serializers.SerializerMethodField()
    price_options = serializers.SerializerMethodField()
    publication_state = serializers.CharField(read_only=True)
    before_image_url = serializers.SerializerMethodField()
    after_image_url = serializers.SerializerMethodField()
    result_photo_customer_email = serializers.EmailField(
        source="result_photo_customer.email", read_only=True, default=""
    )
    result_photo_customer_name = serializers.CharField(
        source="result_photo_customer.full_name", read_only=True, default=""
    )

    class Meta:
        model = Service
        fields = (
            "id", "name", "slug", "category_id", "category_name",
            "short_description", "description", "price_type", "price",
            "maximum_price", "pricing_notes", "duration_minutes", "image_path",
            "is_clinic_service", "is_home_service", "requires_full_payment",
            "allows_pay_at_clinic", "is_consultation", "is_featured",
            "is_active", "is_published", "branch_ids", "created_at", "updated_at",
            "price_options", "publication_state",
            "before_image_url", "after_image_url",
            "result_photo_consent_confirmed", "result_photo_consent_reference",
            "result_images_approved",
            "result_photo_customer_email", "result_photo_customer_name",
        )
        read_only_fields = fields

    def get_branch_ids(self, service):
        return [
            str(availability.branch_id)
            for availability in service.branch_availability.all()
            if availability.is_available and availability.branch.is_active
        ]

    def get_image_path(self, service):
        if service.image:
            return service.image.url
        return service.image_path

    def get_price_options(self, service):
        options = [option for option in service.price_options.all() if option.is_active]
        return ServicePriceOptionSerializer(options, many=True).data

    def get_before_image_url(self, service):
        return service.before_image.url if service.before_image else None

    def get_after_image_url(self, service):
        return service.after_image.url if service.after_image else None


class ManagementServiceCategorySerializer(serializers.ModelSerializer):
    service_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = ServiceCategory
        fields = (
            "id", "name", "slug", "description", "display_order",
            "is_active", "service_count", "created_at", "updated_at",
        )
        read_only_fields = ("id", "slug", "service_count", "created_at", "updated_at")

    def _unique_slug(self, name):
        base = slugify(name) or "category"
        slug = base
        counter = 2
        while ServiceCategory.objects.filter(slug=slug).exists():
            slug = f"{base}-{counter}"
            counter += 1
        return slug

    def create(self, validated_data):
        return ServiceCategory.objects.create(
            slug=self._unique_slug(validated_data["name"]),
            **validated_data,
        )
