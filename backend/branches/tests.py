from datetime import time

from django.test import TestCase

from .models import Branch


class BranchModelTests(TestCase):
    def test_code_is_normalized_to_uppercase(self):
        branch = Branch.objects.create(
            name="Makola",
            code="makola",
            address="Makola Shopping Mall, Accra",
            telephone_number="+233000000000",
            opening_days=["monday", "tuesday"],
            opening_time=time(7, 30),
            closing_time=time(17, 0),
        )

        self.assertEqual(branch.code, "MAKOLA")

# Create your tests here.
