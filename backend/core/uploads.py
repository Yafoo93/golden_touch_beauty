from rest_framework import serializers


MAX_IMAGE_UPLOAD_BYTES = 8 * 1024 * 1024
ALLOWED_IMAGE_CONTENT_TYPES = {
    "JPEG": "image/jpeg",
    "PNG": "image/png",
    "WEBP": "image/webp",
}


def validate_image_upload(image, *, declared_content_type=None):
    """Validate upload size, declared MIME type, and decoded image format."""
    if image.size > MAX_IMAGE_UPLOAD_BYTES:
        raise serializers.ValidationError("Images cannot exceed 8 MB.")

    declared_type = str(
        declared_content_type or getattr(image, "content_type", "")
    ).lower()
    decoded_format = str(
        getattr(getattr(image, "image", None), "format", "")
    ).upper()
    expected_type = ALLOWED_IMAGE_CONTENT_TYPES.get(decoded_format)

    if not expected_type:
        raise serializers.ValidationError("Upload a JPEG, PNG, or WebP image.")
    if declared_type != expected_type:
        raise serializers.ValidationError(
            "The file content does not match its declared image type."
        )
    return image


class RestrictedImageField(serializers.ImageField):
    """Image field that validates size before decode and preserves client MIME."""

    def to_internal_value(self, data):
        if getattr(data, "size", 0) > MAX_IMAGE_UPLOAD_BYTES:
            raise serializers.ValidationError("Images cannot exceed 8 MB.")
        declared_content_type = getattr(data, "content_type", "")
        image = super().to_internal_value(data)
        return validate_image_upload(
            image,
            declared_content_type=declared_content_type,
        )
