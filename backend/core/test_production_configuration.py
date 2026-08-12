from django.core.exceptions import ImproperlyConfigured
from django.test import SimpleTestCase

from config.settings.production_validation import validate_production_settings


SAFE_SETTINGS = {
    "secret_key": "a-unique-production-secret-key-with-at-least-fifty-characters-123",
    "allowed_hosts": ["api.example.com"],
    "csrf_trusted_origins": ["https://www.example.com"],
    "frontend_url": "https://www.example.com",
    "database_engine": "django.db.backends.postgresql",
}


class ProductionConfigurationTests(SimpleTestCase):
    def test_safe_configuration_is_accepted(self):
        validate_production_settings(**SAFE_SETTINGS)

    def test_wildcard_or_local_hosts_are_rejected(self):
        for hosts in (["*"], ["localhost"], ["http://api.example.com/path"]):
            with self.subTest(hosts=hosts), self.assertRaises(ImproperlyConfigured):
                validate_production_settings(**{**SAFE_SETTINGS, "allowed_hosts": hosts})

    def test_insecure_frontend_or_csrf_origins_are_rejected(self):
        unsafe_cases = (
            {"frontend_url": "http://www.example.com"},
            {"csrf_trusted_origins": ["http://www.example.com"]},
            {"csrf_trusted_origins": ["https://other.example.com"]},
        )
        for changes in unsafe_cases:
            with self.subTest(changes=changes), self.assertRaises(ImproperlyConfigured):
                validate_production_settings(**{**SAFE_SETTINGS, **changes})

    def test_short_secret_and_non_postgresql_database_are_rejected(self):
        for changes in (
            {"secret_key": "too-short"},
            {"database_engine": "django.db.backends.sqlite3"},
        ):
            with self.subTest(changes=changes), self.assertRaises(ImproperlyConfigured):
                validate_production_settings(**{**SAFE_SETTINGS, **changes})
