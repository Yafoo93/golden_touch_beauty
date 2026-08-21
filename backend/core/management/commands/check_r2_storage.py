import uuid

from django.conf import settings
from django.core.files.base import ContentFile
from django.core.files.storage import storages
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = "Verify read/write/delete access to both R2 media buckets."

    def handle(self, *args, **options):
        if not settings.USE_R2_STORAGE:
            raise CommandError("R2 storage is disabled. Set USE_R2_STORAGE=True first.")

        for alias in ("public_media", "private_media"):
            storage = storages[alias]
            key = f"system/storage-checks/{uuid.uuid4().hex}.txt"
            saved_key = None
            try:
                saved_key = storage.save(key, ContentFile(b"storage-check"))
                if not storage.exists(saved_key):
                    raise CommandError(f"{alias} upload could not be verified.")
                with storage.open(saved_key, "rb") as stored_file:
                    if stored_file.read() != b"storage-check":
                        raise CommandError(f"{alias} download verification failed.")
            except CommandError:
                raise
            except Exception as exc:
                raise CommandError(f"{alias} storage check failed: {exc}") from exc
            finally:
                if saved_key:
                    storage.delete(saved_key)

            self.stdout.write(self.style.SUCCESS(f"{alias}: read/write/delete passed"))
