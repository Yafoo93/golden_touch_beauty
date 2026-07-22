from datetime import time

from django.core.exceptions import ValidationError
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.request import Request
from rest_framework.test import APIRequestFactory, force_authenticate

from accounts.models import User
from bookings.models import Booking
from inventory.models import BranchInventory
from orders.models import Order
from payments.models import Payment, Receipt
from pos.models import POSSale
from reports.models import ReportSnapshot

from .models import Branch, BranchStaffAssignment
from .permissions import (
    IsOwnerOrAssignedBranchStaff,
    can_access_branch,
    filter_queryset_by_branch_access,
    get_accessible_branch_ids,
)


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


class BranchStaffAssignmentModelTests(TestCase):
    def setUp(self):
        self.makola = Branch.objects.create(name="Makola", code="MAKOLA", address="Accra", telephone_number="+233200000000", opening_days=["monday"], opening_time=time(7, 30), closing_time=time(17, 0))
        self.tse_addo = Branch.objects.create(name="Tse Addo", code="TSE-ADDO", address="Accra", telephone_number="+233200000001", opening_days=["monday"], opening_time=time(7, 30), closing_time=time(19, 0))
        self.staff = User.objects.create_user(email="cashier@example.com", phone_number="+233200000002", full_name="Cashier", password="test-password", is_staff=True)
        self.customer = User.objects.create_user(email="customer@example.com", phone_number="+233200000003", full_name="Customer", password="test-password")

    def test_staff_can_have_multiple_roles_and_branch_assignments(self):
        makola_assignment = BranchStaffAssignment.objects.create(
            branch=self.makola,
            staff=self.staff,
            roles=["cashier", "receptionist"],
            permission_overrides={"can_refund": False},
        )
        BranchStaffAssignment.objects.create(
            branch=self.tse_addo,
            staff=self.staff,
            roles=["cashier"],
        )

        self.assertEqual(makola_assignment.roles, ["cashier", "receptionist"])
        self.assertEqual(self.staff.branch_assignments.count(), 2)

    def test_duplicate_membership_is_rejected(self):
        BranchStaffAssignment.objects.create(branch=self.makola, staff=self.staff, roles=["cashier"])
        with self.assertRaises(ValidationError):
            BranchStaffAssignment.objects.create(branch=self.makola, staff=self.staff, roles=["manager"])

    def test_non_staff_account_cannot_be_assigned(self):
        with self.assertRaises(ValidationError):
            BranchStaffAssignment.objects.create(branch=self.makola, staff=self.customer, roles=["cashier"])

    def test_assignment_requires_valid_roles(self):
        with self.assertRaises(ValidationError):
            BranchStaffAssignment.objects.create(branch=self.makola, staff=self.staff, roles=[])
        with self.assertRaises(ValidationError):
            BranchStaffAssignment.objects.create(branch=self.makola, staff=self.staff, roles=["invented-role"])


class BranchAccessPermissionTests(TestCase):
    def setUp(self):
        self.makola = Branch.objects.create(name="Makola", code="MAKOLA", address="Accra", telephone_number="+233200000000", opening_days=["monday"], opening_time=time(7, 30), closing_time=time(17, 0))
        self.tse_addo = Branch.objects.create(name="Tse Addo", code="TSE-ADDO", address="Accra", telephone_number="+233200000001", opening_days=["monday"], opening_time=time(7, 30), closing_time=time(19, 0))
        self.staff = User.objects.create_user(email="makola@example.com", phone_number="+233200000004", full_name="Makola Cashier", password="test-password", is_staff=True)
        self.owner = User.objects.create_superuser(email="owner2@example.com", phone_number="+233200000005", full_name="Owner", password="test-password")
        self.assignment = BranchStaffAssignment.objects.create(branch=self.makola, staff=self.staff, roles=["cashier"])

    def test_staff_can_access_only_assigned_branch(self):
        self.assertTrue(can_access_branch(self.staff, self.makola))
        self.assertFalse(can_access_branch(self.staff, self.tse_addo))
        self.assertEqual(get_accessible_branch_ids(self.staff), {self.makola.id})

    def test_required_roles_are_enforced(self):
        self.assertTrue(can_access_branch(self.staff, self.makola, ["cashier"]))
        self.assertFalse(can_access_branch(self.staff, self.makola, ["manager"]))

    def test_owner_has_global_access_and_staff_queryset_is_scoped(self):
        staff_branches = filter_queryset_by_branch_access(Branch.objects.all(), self.staff, branch_lookup="")
        owner_branches = filter_queryset_by_branch_access(Branch.objects.all(), self.owner, branch_lookup="")
        self.assertEqual(set(staff_branches), {self.makola})
        self.assertEqual(set(owner_branches), {self.makola, self.tse_addo})

    def test_inactive_assignment_and_explicit_deny_remove_access(self):
        self.assignment.is_active = False
        self.assignment.save()
        self.assertFalse(can_access_branch(self.staff, self.makola))
        self.assignment.is_active = True
        self.assignment.permission_overrides = {"can_access_branch": False}
        self.assignment.save()
        self.assertFalse(can_access_branch(self.staff, self.makola))

    def test_object_permission_rejects_cross_branch_access(self):
        request = APIRequestFactory().get("/")
        force_authenticate(request, user=self.staff)
        request = Request(request)
        view = type("BranchView", (), {"kwargs": {}, "required_branch_roles": ("cashier",)})()
        permission = IsOwnerOrAssignedBranchStaff()
        self.assertTrue(permission.has_permission(request, view))
        self.assertTrue(permission.has_object_permission(request, view, self.makola))
        self.assertFalse(permission.has_object_permission(request, view, self.tse_addo))


class OperationalBranchAttributionTests(TestCase):
    def test_every_operational_record_has_a_required_protected_branch(self):
        models = (Booking, Order, Payment, Receipt, POSSale, ReportSnapshot, BranchInventory)
        for model in models:
            with self.subTest(model=model.__name__):
                branch_field = model._meta.get_field("branch")
                self.assertFalse(branch_field.null)
                self.assertEqual(branch_field.remote_field.on_delete.__name__, "PROTECT")


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


class ManagementBranchApiTests(TestCase):
    def setUp(self):
        self.branch = Branch.objects.create(name="Inactive Branch", code="INACTIVE", address="Internal address", telephone_number="+233000000000", opening_days=["monday"], opening_time=time(8, 0), closing_time=time(16, 0), is_active=False)
        self.owner = User.objects.create_superuser(email="owner@example.com", phone_number="+233111111111", full_name="Business Owner", password="test-password")
        self.staff = User.objects.create_user(email="staff@example.com", phone_number="+233222222222", full_name="Branch Staff", password="test-password", is_staff=True)

    def test_anonymous_user_cannot_list_management_branches(self):
        response = self.client.get(reverse("branches:management-list"))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_non_owner_staff_cannot_list_management_branches(self):
        self.client.force_login(self.staff)
        response = self.client.get(reverse("branches:management-list"))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_owner_can_list_active_and_inactive_branches(self):
        self.client.force_login(self.owner)
        response = self.client.get(reverse("branches:management-list"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()["count"], 1)
        branch = response.json()["results"][0]
        self.assertEqual(branch["code"], "INACTIVE")
        self.assertFalse(branch["is_active"])
        self.assertIn("assigned_manager", branch)

    def test_owner_can_create_branch(self):
        self.client.force_login(self.owner)
        response = self.client.post(
            reverse("branches:management-list"),
            {
                "name": "East Legon",
                "code": "east-legon",
                "address": "East Legon, Accra",
                "telephone_number": "+233200000000",
                "whatsapp_number": "+233200000000",
                "opening_days": ["monday", "tuesday", "saturday"],
                "opening_time": "08:00",
                "closing_time": "18:00",
                "is_active": True,
            },
            content_type="application/json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.json()["code"], "EAST-LEGON")
        self.assertTrue(Branch.objects.filter(code="EAST-LEGON").exists())

    def test_non_owner_cannot_create_branch(self):
        self.client.force_login(self.staff)
        response = self.client.post(
            reverse("branches:management-list"),
            {},
            content_type="application/json",
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_closing_time_must_be_after_opening_time(self):
        self.client.force_login(self.owner)
        response = self.client.post(
            reverse("branches:management-list"),
            {
                "name": "Invalid Hours",
                "code": "INVALID-HOURS",
                "address": "Accra",
                "telephone_number": "+233200000000",
                "opening_days": ["monday"],
                "opening_time": "18:00",
                "closing_time": "08:00",
            },
            content_type="application/json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("closing_time", response.json()["error"]["details"])

    def test_owner_can_retrieve_and_update_branch(self):
        self.client.force_login(self.owner)
        detail_url = reverse("branches:management-detail", args=[self.branch.pk])

        detail_response = self.client.get(detail_url)
        self.assertEqual(detail_response.status_code, status.HTTP_200_OK)
        self.assertEqual(detail_response.json()["code"], "INACTIVE")

        update_response = self.client.patch(
            detail_url,
            {
                "telephone_number": "+233244444444",
                "closing_time": "17:30",
                "assigned_manager_id": str(self.staff.pk),
                "is_active": True,
            },
            content_type="application/json",
        )
        self.assertEqual(update_response.status_code, status.HTTP_200_OK)
        self.branch.refresh_from_db()
        self.assertEqual(self.branch.telephone_number, "+233244444444")
        self.assertEqual(self.branch.assigned_manager, self.staff)
        self.assertTrue(self.branch.is_active)
        assignment = BranchStaffAssignment.objects.get(branch=self.branch, staff=self.staff)
        self.assertEqual(assignment.roles, [BranchStaffAssignment.Role.MANAGER])
        self.assertEqual(assignment.assigned_by, self.owner)

    def test_non_owner_cannot_update_branch(self):
        self.client.force_login(self.staff)
        response = self.client.patch(
            reverse("branches:management-detail", args=[self.branch.pk]),
            {"is_active": True},
            content_type="application/json",
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_owner_can_list_eligible_branch_managers(self):
        self.client.force_login(self.owner)
        response = self.client.get(reverse("branches:management-manager-options"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        ids = {manager["id"] for manager in response.json()}
        self.assertIn(str(self.owner.pk), ids)
        self.assertIn(str(self.staff.pk), ids)

# Create your tests here.
