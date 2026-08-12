from datetime import time, timedelta

from django.core.exceptions import ValidationError
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.request import Request
from rest_framework.test import APIRequestFactory, force_authenticate

from accounts.models import User
from bookings.models import Booking, BookingServiceItem
from inventory.models import BranchInventory
from orders.models import Order, OrderItem
from payments.models import Invoice, Payment, Receipt
from pos.models import POSSale
from products.models import Product, ProductCategory, ProductVariant
from reports.models import ReportSnapshot
from services.models import Service, ServiceCategory

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

    def test_branch_contact_numbers_are_normalized(self):
        self.client.force_login(self.owner)
        response = self.client.post(
            reverse("branches:management-list"),
            {
                "name": "Normalized Contacts",
                "code": "NORMALIZED",
                "address": "Accra",
                "telephone_number": "024 137 0429",
                "secondary_telephone_number": "00 233 25 771 1182",
                "whatsapp_number": "(024) 137-0429",
                "opening_days": ["monday"],
                "opening_time": "08:00",
                "closing_time": "18:00",
            },
            content_type="application/json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        branch = Branch.objects.get(code="NORMALIZED")
        self.assertEqual(branch.telephone_number, "+233241370429")
        self.assertEqual(branch.secondary_telephone_number, "+233257711182")
        self.assertEqual(branch.whatsapp_number, "+233241370429")

    def test_invalid_branch_contact_number_is_rejected(self):
        self.client.force_login(self.owner)
        response = self.client.post(
            reverse("branches:management-list"),
            {
                "name": "Invalid Contact",
                "code": "INVALID-CONTACT",
                "address": "Accra",
                "telephone_number": "123",
                "opening_days": ["monday"],
                "opening_time": "08:00",
                "closing_time": "18:00",
            },
            content_type="application/json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("telephone_number", response.json()["error"]["details"])

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


class ManagementOverviewApiTests(TestCase):
    def setUp(self):
        self.makola = Branch.objects.create(
            name="Overview Makola", code="OVERVIEW-MAKOLA", address="Accra",
            telephone_number="+233200000101", opening_days=["monday"],
            opening_time=time(7, 30), closing_time=time(17, 0),
        )
        self.tse_addo = Branch.objects.create(
            name="Overview Tse Addo", code="OVERVIEW-TSE", address="Accra",
            telephone_number="+233200000102", opening_days=["monday"],
            opening_time=time(7, 30), closing_time=time(19, 0),
        )
        self.owner = User.objects.create_superuser(
            email="overview-owner@example.com", phone_number="+233200000103",
            full_name="Overview Owner", password="test-password",
        )
        self.manager = User.objects.create_user(
            email="overview-manager@example.com", phone_number="+233200000104",
            full_name="Makola Manager", password="test-password", is_staff=True,
        )
        self.cashier = User.objects.create_user(
            email="overview-cashier@example.com", phone_number="+233200000105",
            full_name="Makola Cashier", password="test-password", is_staff=True,
        )
        self.customer = User.objects.create_user(
            email="overview-customer@example.com", phone_number="+233200000106",
            full_name="Overview Customer", password="test-password",
        )
        category = ProductCategory.objects.create(
            name="Overview products", slug="overview-products",
        )
        self.product_category = category
        product = Product.objects.create(
            category=category, name="Overview Cream", slug="overview-cream",
            description="Dashboard inventory fixture.",
            is_active=True, is_published=True,
        )
        standard = ProductVariant.objects.create(
            product=product, name="Standard", sku="OVERVIEW-CREAM-STD",
            selling_price="50.00", cost_price="25.00",
        )
        travel = ProductVariant.objects.create(
            product=product, name="Travel", sku="OVERVIEW-CREAM-TRAVEL",
            selling_price="30.00", cost_price="15.00",
        )
        BranchInventory.objects.create(
            branch=self.makola, product_variant=standard,
            quantity_on_hand=10, quantity_reserved=6, reorder_level=4,
        )
        BranchInventory.objects.create(
            branch=self.tse_addo, product_variant=standard,
            quantity_on_hand=10, quantity_reserved=1, reorder_level=2,
        )
        BranchInventory.objects.create(
            branch=self.tse_addo, product_variant=travel,
            quantity_on_hand=2, quantity_reserved=0, reorder_level=3,
        )
        BranchStaffAssignment.objects.create(
            branch=self.makola, staff=self.manager, roles=["manager"],
        )
        BranchStaffAssignment.objects.create(
            branch=self.makola, staff=self.cashier, roles=["cashier"],
        )
        now = timezone.now()
        today_booking = Booking.objects.create(
            branch=self.makola, customer=self.customer,
            status=Booking.Status.CONFIRMED, preferred_start=now,
            recipient_name=self.customer.full_name,
            recipient_phone=self.customer.phone_number,
        )
        self.service_category = ServiceCategory.objects.create(
            name="Overview services", slug="overview-services",
        )
        service = Service.objects.create(
            category=self.service_category,
            name="Overview Facial",
            slug="overview-facial",
            short_description="Dashboard service fixture.",
            description="Dashboard service fixture.",
            price="60.00",
            duration_minutes=60,
            is_active=True,
            is_published=True,
        )
        BookingServiceItem.objects.create(
            booking=today_booking,
            service=service,
            service_name=service.name,
            unit_price="60.00",
            duration_minutes=60,
        )
        Booking.objects.create(
            branch=self.tse_addo, customer=self.customer,
            status=Booking.Status.PENDING, preferred_start=now,
            recipient_name=self.customer.full_name,
            recipient_phone=self.customer.phone_number,
        )
        Booking.objects.create(
            branch=self.makola, customer=self.customer,
            status=Booking.Status.CANCELLED, preferred_start=now,
            recipient_name=self.customer.full_name,
            recipient_phone=self.customer.phone_number,
        )
        Booking.objects.create(
            branch=self.makola, customer=self.customer,
            status=Booking.Status.CONFIRMED,
            preferred_start=now + timedelta(days=1),
            recipient_name=self.customer.full_name,
            recipient_phone=self.customer.phone_number,
        )
        Booking.objects.create(
            branch=self.makola, customer=self.customer,
            status=Booking.Status.PENDING,
            preferred_start=now + timedelta(days=2),
            recipient_name=self.customer.full_name,
            recipient_phone=self.customer.phone_number,
        )
        Booking.objects.create(
            branch=self.makola, customer=self.customer,
            status=Booking.Status.PROPOSED,
            preferred_start=now + timedelta(days=3),
            proposed_start=now + timedelta(days=3, hours=1),
            proposed_expires_at=now + timedelta(days=1),
            recipient_name=self.customer.full_name,
            recipient_phone=self.customer.phone_number,
        )
        makola_order = Order.objects.create(
            branch=self.makola, customer=self.customer,
            status=Order.Status.PAID, payment_status="paid",
            subtotal="100.00", total_amount="100.00",
            recipient_name=self.customer.full_name,
            recipient_phone=self.customer.phone_number,
            paid_at=now,
        )
        tse_addo_order = Order.objects.create(
            branch=self.tse_addo, customer=self.customer,
            status=Order.Status.PAID, payment_status="paid",
            subtotal="75.50", total_amount="75.50",
            recipient_name=self.customer.full_name,
            recipient_phone=self.customer.phone_number,
            paid_at=now,
        )
        for order, variant, amount in (
            (makola_order, standard, "100.00"),
            (tse_addo_order, travel, "75.50"),
        ):
            OrderItem.objects.create(
                order=order,
                product_variant=variant,
                product_name=variant.product.name,
                product_slug=variant.product.slug,
                variant_name=variant.name,
                sku=variant.sku,
                unit_price=amount,
                quantity=1,
                line_total=amount,
            )
        Payment.objects.create(
            branch=self.makola, customer=self.customer, order=makola_order,
            status=Payment.Status.SUCCEEDED, amount="100.00", currency="GHS",
            paid_at=now,
        )
        Payment.objects.create(
            branch=self.tse_addo, customer=self.customer, order=tse_addo_order,
            status=Payment.Status.SUCCEEDED, amount="75.50", currency="GHS",
            paid_at=now,
        )
        Payment.objects.create(
            branch=self.makola, customer=self.customer, order=makola_order,
            status=Payment.Status.PENDING, amount="20.00", currency="GHS",
            paid_at=None,
        )
        Payment.objects.create(
            branch=self.makola, customer=self.customer,
            status=Payment.Status.SUCCEEDED, amount="50.00", currency="GHS",
            paid_at=now - timedelta(days=1),
        )
        Payment.objects.create(
            branch=self.makola, customer=self.customer, order=makola_order,
            status=Payment.Status.REFUNDED, amount="30.00", currency="GHS",
            paid_at=now,
        )
        makola_paid_booking = Booking.objects.create(
            branch=self.makola, customer=self.customer,
            status=Booking.Status.COMPLETED,
            preferred_start=now - timedelta(days=1), total_amount="60.00",
            payment_status="paid", recipient_name=self.customer.full_name,
            recipient_phone=self.customer.phone_number,
        )
        tse_addo_paid_booking = Booking.objects.create(
            branch=self.tse_addo, customer=self.customer,
            status=Booking.Status.COMPLETED,
            preferred_start=now - timedelta(days=1), total_amount="40.00",
            payment_status="paid", recipient_name=self.customer.full_name,
            recipient_phone=self.customer.phone_number,
        )
        for booking in (makola_paid_booking, tse_addo_paid_booking):
            BookingServiceItem.objects.create(
                booking=booking,
                service=service,
                service_name=service.name,
                unit_price=booking.total_amount,
                duration_minutes=60,
            )
        Payment.objects.create(
            branch=self.makola, customer=self.customer,
            booking=makola_paid_booking, status=Payment.Status.SUCCEEDED,
            amount="60.00", currency="GHS", paid_at=now - timedelta(days=1),
        )
        Payment.objects.create(
            branch=self.tse_addo, customer=self.customer,
            booking=tse_addo_paid_booking, status=Payment.Status.SUCCEEDED,
            amount="40.00", currency="GHS", paid_at=now - timedelta(days=1),
        )
        Payment.objects.create(
            branch=self.makola, customer=self.customer,
            booking=makola_paid_booking, status=Payment.Status.REFUNDED,
            amount="15.00", currency="GHS", paid_at=now - timedelta(days=1),
        )

        def create_invoice(branch, amount, invoice_status):
            order = Order.objects.create(
                branch=branch, customer=self.customer,
                subtotal=amount, total_amount=amount,
                recipient_name=self.customer.full_name,
                recipient_phone=self.customer.phone_number,
            )
            return Invoice.objects.create(
                branch=branch, customer=self.customer, order=order,
                source_type="order", source_reference=order.reference,
                recipient_name=self.customer.full_name,
                recipient_email=self.customer.email,
                subtotal=amount, total_amount=amount, currency="GHS",
                line_items=[], status=invoice_status,
            )

        create_invoice(self.makola, "90.00", Invoice.Status.OPEN)
        create_invoice(self.tse_addo, "60.00", Invoice.Status.OPEN)
        create_invoice(self.makola, "30.00", Invoice.Status.PAID)
        create_invoice(self.makola, "25.00", Invoice.Status.EXPIRED)
        Order.objects.create(
            branch=self.makola, customer=self.customer,
            status=Order.Status.DELIVERED, payment_status="paid",
            recipient_name=self.customer.full_name,
            recipient_phone=self.customer.phone_number,
        )
        Order.objects.create(
            branch=self.tse_addo, customer=self.customer,
            status=Order.Status.CANCELLED, payment_status="cancelled",
            recipient_name=self.customer.full_name,
            recipient_phone=self.customer.phone_number,
        )
        Booking.objects.create(
            branch=self.tse_addo, customer=self.customer,
            status=Booking.Status.PROPOSED,
            preferred_start=now + timedelta(days=4),
            proposed_start=now + timedelta(days=4, hours=1),
            proposed_expires_at=now + timedelta(days=1),
            recipient_name=self.customer.full_name,
            recipient_phone=self.customer.phone_number,
        )
        Booking.objects.create(
            branch=self.makola, customer=self.customer,
            status=Booking.Status.PROPOSED,
            preferred_start=now + timedelta(days=5),
            proposed_start=now + timedelta(days=5, hours=1),
            proposed_expires_at=now - timedelta(minutes=1),
            recipient_name=self.customer.full_name,
            recipient_phone=self.customer.phone_number,
        )

    def test_owner_overview_contains_every_branch(self):
        self.client.force_login(self.owner)
        response = self.client.get(reverse("branches:management-overview"))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.json()["staff"]["is_owner"])
        self.assertEqual(
            {branch["code"] for branch in response.json()["branches"]},
            {self.makola.code, self.tse_addo.code},
        )
        self.assertEqual(response.json()["summary"]["today_appointments"], 2)
        self.assertEqual(response.json()["summary"]["pending_booking_requests"], 2)
        self.assertEqual(
            response.json()["summary"]["proposed_changes_awaiting_acceptance"],
            2,
        )
        self.assertEqual(response.json()["summary"]["today_sales"], "175.50")
        self.assertEqual(response.json()["summary"]["product_revenue"], "175.50")
        self.assertEqual(response.json()["summary"]["service_revenue"], "100.00")
        self.assertEqual(response.json()["summary"]["outstanding_balances"], "150.00")
        self.assertEqual(response.json()["summary"]["pending_online_orders"], 6)
        self.assertEqual(response.json()["summary"]["low_stock_products"], 2)
        self.assertEqual(
            {item["code"] for item in response.json()["branch_comparison"]},
            {self.makola.code, self.tse_addo.code},
        )

    def test_manager_overview_is_limited_to_assigned_branches(self):
        self.client.force_login(self.manager)
        response = self.client.get(reverse("branches:management-overview"))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(response.json()["staff"]["is_owner"])
        self.assertEqual(
            [branch["code"] for branch in response.json()["branches"]],
            [self.makola.code],
        )
        self.assertEqual(response.json()["branches"][0]["roles"], ["manager"])
        self.assertEqual(response.json()["summary"]["today_appointments"], 1)
        self.assertEqual(response.json()["summary"]["pending_booking_requests"], 1)
        self.assertEqual(
            response.json()["summary"]["proposed_changes_awaiting_acceptance"],
            1,
        )
        self.assertEqual(response.json()["summary"]["today_sales"], "100.00")
        self.assertEqual(response.json()["summary"]["product_revenue"], "100.00")
        self.assertEqual(response.json()["summary"]["service_revenue"], "60.00")
        self.assertEqual(response.json()["summary"]["outstanding_balances"], "90.00")
        self.assertEqual(response.json()["summary"]["pending_online_orders"], 4)
        self.assertEqual(response.json()["summary"]["low_stock_products"], 1)

    def test_owner_can_filter_overview_to_one_authorized_branch(self):
        self.client.force_login(self.owner)
        response = self.client.get(
            reverse("branches:management-overview"),
            {"branch": str(self.makola.pk)},
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()["summary"]["today_sales"], "100.00")
        self.assertEqual(response.json()["summary"]["low_stock_products"], 1)
        self.assertEqual(
            [branch["id"] for branch in response.json()["branches"]],
            [str(self.makola.pk)],
        )

    def test_manager_cannot_filter_to_an_unassigned_branch(self):
        self.client.force_login(self.manager)
        response = self.client.get(
            reverse("branches:management-overview"),
            {"branch": str(self.tse_addo.pk)},
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_status_and_payment_method_filters_change_relevant_metrics(self):
        self.client.force_login(self.owner)
        booking_response = self.client.get(
            reverse("branches:management-overview"),
            {"booking_status": Booking.Status.CONFIRMED},
        )
        order_response = self.client.get(
            reverse("branches:management-overview"),
            {"order_status": Order.Status.CANCELLED},
        )
        payment_response = self.client.get(
            reverse("branches:management-overview"),
            {"payment_method": "not-used"},
        )

        self.assertEqual(booking_response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            booking_response.json()["summary"]["pending_booking_requests"], 0
        )
        self.assertEqual(order_response.status_code, status.HTTP_200_OK)
        self.assertEqual(order_response.json()["summary"]["pending_online_orders"], 0)
        self.assertEqual(payment_response.status_code, status.HTTP_200_OK)
        self.assertEqual(payment_response.json()["summary"]["today_sales"], "0.00")

    def test_category_filters_exclude_unrelated_revenue(self):
        self.client.force_login(self.owner)
        product_response = self.client.get(
            reverse("branches:management-overview"),
            {"product_category": str(self.product_category.pk)},
        )
        service_response = self.client.get(
            reverse("branches:management-overview"),
            {"service_category": str(self.service_category.pk)},
        )

        self.assertEqual(product_response.status_code, status.HTTP_200_OK)
        self.assertEqual(product_response.json()["summary"]["product_revenue"], "175.50")
        self.assertEqual(product_response.json()["summary"]["service_revenue"], "0.00")
        self.assertEqual(product_response.json()["summary"]["low_stock_products"], 2)
        self.assertEqual(service_response.status_code, status.HTTP_200_OK)
        self.assertEqual(service_response.json()["summary"]["service_revenue"], "100.00")
        self.assertEqual(service_response.json()["summary"]["product_revenue"], "0.00")

    def test_selected_branch_keeps_all_authorized_branch_options(self):
        self.client.force_login(self.owner)
        response = self.client.get(
            reverse("branches:management-overview"),
            {"branch": str(self.makola.pk)},
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            {item["id"] for item in response.json()["filter_options"]["branches"]},
            {str(self.makola.pk), str(self.tse_addo.pk)},
        )

    def test_date_range_is_validated_and_filter_options_are_returned(self):
        self.client.force_login(self.owner)
        invalid_response = self.client.get(
            reverse("branches:management-overview"),
            {"date_from": "2026-08-12", "date_to": "2026-08-01"},
        )
        response = self.client.get(reverse("branches:management-overview"))

        self.assertEqual(invalid_response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        options = response.json()["filter_options"]
        self.assertTrue(options["product_categories"])
        self.assertEqual(
            {item["value"] for item in options["booking_statuses"]},
            set(Booking.Status.values),
        )
        self.assertEqual(
            {item["value"] for item in options["order_statuses"]},
            set(Order.Status.values),
        )

    def test_cashier_without_management_role_cannot_open_overview(self):
        self.client.force_login(self.cashier)
        response = self.client.get(reverse("branches:management-overview"))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

# Create your tests here.
