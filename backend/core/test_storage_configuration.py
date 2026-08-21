from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.test import SimpleTestCase

from bookings.models import Booking, booking_intake_path
from config.settings.storage_validation import validate_r2_settings
from core.models import GalleryItem
from core.storage import private_media_storage, public_media_storage
from products.models import Product
from services.models import Service


SAFE_R2_SETTINGS = {
    "endpoint_url": "https://account.r2.cloudflarestorage.com",
    "public_bucket": "public-media",
    "private_bucket": "private-media",
    "public_custom_domain": "media.example.com",
    "private_url_expiry": 300,
}


class R2ConfigurationTests(SimpleTestCase):
    def test_safe_configuration_is_accepted(self):
        validate_r2_settings(**SAFE_R2_SETTINGS)

    def test_unsafe_configuration_is_rejected(self):
        unsafe_cases = (
            {"endpoint_url": "http://account.r2.cloudflarestorage.com"},
            {"private_bucket": "public-media"},
            {"public_bucket": "public-media/"},
            {"public_custom_domain": "https://media.example.com"},
            {"private_url_expiry": 86400},
        )
        for changes in unsafe_cases:
            with self.subTest(changes=changes), self.assertRaises(ImproperlyConfigured):
                validate_r2_settings(**{**SAFE_R2_SETTINGS, **changes})

    def test_public_models_explicitly_use_public_storage(self):
        for model in (Product, Service, GalleryItem):
            with self.subTest(model=model.__name__):
                field = model._meta.get_field("image")
                self.assertIs(field._storage_callable, public_media_storage)

    def test_treatment_photos_explicitly_use_private_storage(self):
        field = Booking._meta.get_field("treatment_photo")
        self.assertIs(field._storage_callable, private_media_storage)

    def test_default_storage_fails_closed(self):
        self.assertEqual(settings.STORAGES["default"], settings.STORAGES["private_media"])
        if settings.USE_R2_STORAGE:
            self.assertNotEqual(
                settings.STORAGES["public_media"], settings.STORAGES["private_media"]
            )

    def test_treatment_photo_keys_are_private_and_randomized(self):
        first = booking_intake_path(None, "client-name.JPG")
        second = booking_intake_path(None, "client-name.JPG")
        self.assertTrue(first.startswith("private/booking-intake/"))
        self.assertTrue(first.endswith(".jpg"))
        self.assertNotEqual(first, second)
