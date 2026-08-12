import base64

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import SimpleTestCase
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers

from bookings.serializers import BookingCreateSerializer
from products.serializers import (
    ManagementProductCreateSerializer,
    ManagementProductUpdateSerializer,
)
from services.serializers import ManagementServiceCreateSerializer

from .serializers import ManagementGalleryItemSerializer
from .uploads import MAX_IMAGE_UPLOAD_BYTES, RestrictedImageField


PNG = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk+A8AAQUBAScY42YAAAAASUVORK5CYII="
)
GIF = base64.b64decode("R0lGODlhAQABAIAAAAAAAP///ywAAAAAAQABAAACAUwAOw==")


def upload(name, payload, content_type):
    return SimpleUploadedFile(name, payload, content_type=content_type)


class UploadRestrictionTests(SimpleTestCase):
    upload_fields = (
        (ManagementGalleryItemSerializer, "image"),
        (ManagementServiceCreateSerializer, "image"),
        (ManagementProductCreateSerializer, "image"),
        (ManagementProductUpdateSerializer, "image"),
        (BookingCreateSerializer, "treatment_photo"),
    )

    def test_supported_png_with_matching_content_type_is_accepted(self):
        image = upload("image.png", PNG, "image/png")
        self.assertIsInstance(RestrictedImageField().run_validation(image), object)

    def test_non_image_content_is_rejected_even_when_named_png(self):
        with self.assertRaises((serializers.ValidationError, DjangoValidationError)):
            RestrictedImageField().run_validation(
                upload("disguised.png", b"This is not an image.", "image/png")
            )

    def test_unsupported_decoded_image_format_is_rejected_by_every_upload(self):
        for serializer_class, field_name in self.upload_fields:
            with self.subTest(serializer=serializer_class.__name__):
                with self.assertRaisesMessage(
                    serializers.ValidationError,
                    "Upload a JPEG, PNG, or WebP image.",
                ):
                    serializer_class().fields[field_name].run_validation(
                        upload("animation.gif", GIF, "image/gif")
                    )

    def test_mime_type_must_match_the_decoded_file(self):
        with self.assertRaisesMessage(
            serializers.ValidationError,
            "The file content does not match its declared image type.",
        ):
            RestrictedImageField().run_validation(
                upload("mislabelled.jpg", PNG, "image/jpeg")
            )

    def test_every_upload_rejects_files_larger_than_eight_megabytes(self):
        for serializer_class, field_name in self.upload_fields:
            with self.subTest(serializer=serializer_class.__name__):
                # Size is checked before decoding, so this also avoids processing
                # an attacker-controlled oversized image in application code.
                with self.assertRaisesMessage(
                    serializers.ValidationError,
                    "Images cannot exceed 8 MB.",
                ):
                    serializer_class().fields[field_name].run_validation(
                        upload(
                            "oversized.png",
                            PNG + b"\0" * (MAX_IMAGE_UPLOAD_BYTES + 1),
                            "image/png",
                        )
                    )
