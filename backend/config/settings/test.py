from .base import *  # noqa: F403


# Tests must never read from or write to real object-storage buckets, even when
# a developer's local .env enables R2 for manual integration testing.
USE_R2_STORAGE = False
_test_media_storage = {
    "BACKEND": "django.core.files.storage.FileSystemStorage",
    "OPTIONS": {
        "location": MEDIA_ROOT,  # noqa: F405
        "base_url": MEDIA_URL,  # noqa: F405
    },
}
STORAGES = {  # noqa: F405
    "default": _test_media_storage,
    "public_media": _test_media_storage,
    "private_media": _test_media_storage,
    "staticfiles": {
        "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage",
    },
}


DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
    }
}

PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.MD5PasswordHasher",
]

EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"
EMAIL_JOBS_EAGER = True
