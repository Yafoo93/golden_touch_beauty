from rest_framework import serializers

from .models import GalleryItem, Testimonial, WebsiteContent
from .uploads import RestrictedImageField, validate_image_upload


class PublicWebsiteContentSerializer(serializers.ModelSerializer):
    class Meta:
        model = WebsiteContent
        fields = ("key", "value")
        read_only_fields = fields


class ManagementWebsiteContentSerializer(serializers.ModelSerializer):
    updated_by = serializers.SerializerMethodField()

    class Meta:
        model = WebsiteContent
        fields = (
            "id", "key", "page", "section", "label", "value",
            "is_published", "updated_by", "updated_at",
        )
        read_only_fields = (
            "id", "key", "page", "section", "label", "updated_by", "updated_at",
        )

    def get_updated_by(self, content):
        if content.updated_by is None:
            return None
        return {
            "id": str(content.updated_by_id),
            "full_name": content.updated_by.full_name,
        }

    def validate_value(self, value):
        value = value.strip()
        if not value:
            raise serializers.ValidationError("Content cannot be empty.")
        if len(value) > 5000:
            raise serializers.ValidationError(
                "Content cannot be longer than 5,000 characters."
            )
        return value


class GalleryItemSerializer(serializers.ModelSerializer):
    image_url = serializers.SerializerMethodField()

    class Meta:
        model = GalleryItem
        fields = (
            "id", "title", "category", "alt_text", "image_url",
            "display_size", "display_order",
        )
        read_only_fields = fields

    def get_image_url(self, item):
        if item.image:
            return f"/{item.image.url.lstrip('/')}"
        return item.image_path


class ManagementGalleryItemSerializer(serializers.ModelSerializer):
    image = RestrictedImageField(write_only=True, required=False)
    image_url = serializers.SerializerMethodField()
    updated_by = serializers.SerializerMethodField()

    class Meta:
        model = GalleryItem
        fields = (
            "id", "title", "category", "alt_text", "image", "image_url",
            "display_size", "display_order", "is_published", "updated_by",
            "created_at", "updated_at",
        )
        read_only_fields = (
            "id", "image_url", "updated_by", "created_at", "updated_at",
        )
        extra_kwargs = {"image": {"write_only": True, "required": False}}

    def get_image_url(self, item):
        if item.image:
            return f"/{item.image.url.lstrip('/')}"
        return item.image_path

    def get_updated_by(self, item):
        if item.updated_by is None:
            return None
        return {"id": str(item.updated_by_id), "full_name": item.updated_by.full_name}

    def validate_image(self, image):
        return validate_image_upload(image)

    def validate(self, attrs):
        if not attrs.get("image") and not (
            self.instance and (self.instance.image or self.instance.image_path)
        ):
            raise serializers.ValidationError({"image": "Upload a gallery image."})
        return attrs


class TestimonialSerializer(serializers.ModelSerializer):
    class Meta:
        model = Testimonial
        fields = (
            "id", "client_name", "client_attribution", "service_context",
            "quote", "is_featured",
        )
        read_only_fields = fields


class ManagementTestimonialSerializer(serializers.ModelSerializer):
    reviewed_by = serializers.SerializerMethodField()
    source_type_label = serializers.CharField(
        source="get_source_type_display",
        read_only=True,
    )

    class Meta:
        model = Testimonial
        fields = (
            "id", "client_name", "client_attribution", "service_context",
            "quote", "source_type", "source_type_label", "consent_confirmed",
            "moderation_status", "is_visible", "is_featured", "display_order",
            "reviewed_by", "reviewed_at", "created_at", "updated_at",
        )
        read_only_fields = (
            "id", "client_name", "client_attribution", "service_context",
            "quote", "source_type", "source_type_label", "reviewed_by",
            "reviewed_at", "created_at", "updated_at",
        )

    def get_reviewed_by(self, testimonial):
        if testimonial.reviewed_by is None:
            return None
        return {
            "id": str(testimonial.reviewed_by_id),
            "full_name": testimonial.reviewed_by.full_name,
        }

    def validate(self, attrs):
        status = attrs.get(
            "moderation_status",
            getattr(self.instance, "moderation_status", Testimonial.ModerationStatus.PENDING),
        )
        consent = attrs.get(
            "consent_confirmed",
            getattr(self.instance, "consent_confirmed", False),
        )
        visible = attrs.get(
            "is_visible",
            getattr(self.instance, "is_visible", False),
        )
        if status == Testimonial.ModerationStatus.APPROVED and not consent:
            raise serializers.ValidationError(
                {"consent_confirmed": "Confirm client consent before approval."}
            )
        if visible and status != Testimonial.ModerationStatus.APPROVED:
            raise serializers.ValidationError(
                {"is_visible": "Only approved testimonials can be visible."}
            )
        if visible and not consent:
            raise serializers.ValidationError(
                {"is_visible": "Confirm client consent before making this visible."}
            )
        return attrs
