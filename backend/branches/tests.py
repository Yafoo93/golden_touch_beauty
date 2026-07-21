from datetime import time

from django.test import TestCase
from django.urls import reverse
from rest_framework import status

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


class PublicBranchApiTests(TestCase):
    def setUp(self):
        self.active_branch = Branch.objects.create(
            name="Makola",
            code="MAKOLA",
            address="Makola Shopping Mall, Accra",
            telephone_number="+233241370429",
            opening_days=["monday", "tuesday"],
            opening_time=time(7, 30),
            closing_time=time(17, 0),
            is_active=True,
        )
        self.inactive_branch = Branch.objects.create(
            name="Closed Branch",
            code="CLOSED",
            address="Not public",
            telephone_number="+233000000000",
            opening_days=["monday"],
            opening_time=time(8, 0),
            closing_time=time(16, 0),
            is_active=False,
        )

    def test_list_is_public_and_contains_only_active_branches(self):
        response = self.client.get(reverse("branches:public-list"))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        codes = {branch["code"] for branch in response.json()["results"]}
        self.assertEqual(codes, {"MAKOLA"})

    def test_detail_does_not_expose_internal_manager_or_active_fields(self):
        response = self.client.get(
            reverse("branches:public-detail", args=[self.active_branch.pk])
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertNotIn("assigned_manager", response.json())
        self.assertNotIn("is_active", response.json())

    def test_inactive_branch_detail_is_not_public(self):
        response = self.client.get(
            reverse("branches:public-detail", args=[self.inactive_branch.pk])
        )

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

# Create your tests here.
