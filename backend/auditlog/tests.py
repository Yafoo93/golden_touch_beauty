from django.core.exceptions import ValidationError
from django.test import TestCase

from .models import AuditLog


class AuditLogModelTests(TestCase):
    def test_existing_entry_cannot_be_changed(self):
        entry = AuditLog.objects.create(
            action="booking.created",
            record_type="booking",
            record_id="BKG-1",
        )
        entry.reason = "Attempted change"

        with self.assertRaisesMessage(ValidationError, "immutable"):
            entry.save()

    def test_entry_cannot_be_deleted(self):
        entry = AuditLog.objects.create(
            action="booking.created",
            record_type="booking",
            record_id="BKG-1",
        )

        with self.assertRaisesMessage(ValidationError, "cannot be deleted"):
            entry.delete()

# Create your tests here.
