"""Route-wide permission policy checks.

This test is deliberately centralized.  Adding an API view without classifying it
below fails CI, which prevents an endpoint from silently inheriting a weaker
default or being published without a security review.
"""

import re

from django.test import SimpleTestCase, TestCase
from django.urls import URLPattern, URLResolver, get_resolver
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.test import APIClient

from accounts.models import User
from branches.permissions import IsOwner, IsOwnerOrAssignedBranchStaff


PUBLIC_VIEWS = {
    "BookingAvailabilityView",
    "CsrfTokenView",
    "EmailVerificationConfirmView",
    "EmailVerificationResendView",
    "FeaturedProductListView",
    "FeaturedServiceListView",
    "LoginView",
    "LogoutView",
    "PasswordResetConfirmView",
    "PasswordResetRequestView",
    "PickupBranchOptionsView",
    "PublicBranchDetailView",
    "PublicBranchListView",
    "PublicGalleryItemListView",
    "PublicProductCategoryListView",
    "PublicProductDetailView",
    "PublicProductListView",
    "PublicServiceCategoryListView",
    "PublicServiceDetailView",
    "PublicServiceListView",
    "PublicTestimonialListView",
    "PublicWebsiteContentListView",
    "RegisterView",
    "health_check",
    "report_client_error",
}

CUSTOMER_VIEWS = {
    "CartValidationView",
    "CheckoutCreateView",
    "CheckoutOptionsView",
    "CurrentUserView",
    "CustomerAccountOverviewView",
    "CustomerAddressDetailView",
    "CustomerAddressListCreateView",
    "CustomerBookingDetailView",
    "CustomerBookingListCreateView",
    "CustomerBookingProposalView",
    "CustomerCartItemDetailView",
    "CustomerCartItemView",
    "CustomerCartView",
    "CustomerConsentView",
    "CustomerOrderCancelView",
    "CustomerOrderDetailView",
    "CustomerOrderListView",
    "CustomerReceiptDetailView",
    "CustomerReceiptListView",
    "NotificationListView",
    "NotificationReadAllView",
    "NotificationReadView",
    "WishlistItemDetailView",
    "WishlistView",
}

OWNER_VIEWS = {
    "BranchManagerOptionListView",
    "ManagementBranchDetailView",
    "ManagementBranchListView",
    "ManagementGalleryItemDetailView",
    "ManagementGalleryItemListCreateView",
    "ManagementProductBranchOptionListView",
    "ManagementProductCategoryDetailView",
    "ManagementProductCategoryListCreateView",
    "ManagementProductCategoryOptionListView",
    "ManagementProductDetailView",
    "ManagementProductListView",
    "ManagementServiceBranchOptionListView",
    "ManagementServiceCategoryDetailView",
    "ManagementServiceCategoryListCreateView",
    "ManagementServiceCategoryOptionListView",
    "ManagementServiceDetailView",
    "ManagementServiceListView",
    "ManagementTestimonialDetailView",
    "ManagementTestimonialListView",
    "ManagementWebsiteContentDetailView",
    "ManagementWebsiteContentListView",
}

BRANCH_SCOPED_VIEWS = {
    "ManagementBookingActionView",
    "ManagementBookingBlockDetailView",
    "ManagementBookingBlockListCreateView",
    "ManagementBookingDetailView",
    "ManagementBookingListCreateView",
    "ManagementBookingOptionsView",
    "ManagementBookingsReportView",
    "ManagementBranchesReportView",
    "ManagementInventoryListView",
    "ManagementInventoryReportView",
    "ManagementOverviewView",
    "ManagementPaymentsReportView",
    "ManagementProductsReportView",
    "ManagementReportExportView",
    "ManagementSalesReportView",
    "ManagementServicesReportView",
    "ManagementStockAdjustmentView",
    "ManagementVariantStockHistoryView",
    "POSCustomerSearchView",
    "POSEndOfDayView",
    "POSSaleCorrectionView",
    "POSSaleDetailView",
    "POSSaleHistoryView",
    "POSWorkspaceView",
}


def api_views(patterns, prefix=""):
    for pattern in patterns:
        route = prefix + str(pattern.pattern)
        if isinstance(pattern, URLResolver):
            yield from api_views(pattern.url_patterns, route)
        elif isinstance(pattern, URLPattern) and route.startswith("api/v1/"):
            callback = pattern.callback
            view_class = getattr(callback, "cls", None) or getattr(
                callback, "view_class", None
            )
            if view_class is not None:
                yield route, view_class


def concrete_test_path(route):
    """Turn a Django route containing converters into a harmless test URL."""
    route = re.sub(
        r"<uuid:[^>]+>",
        "00000000-0000-0000-0000-000000000001",
        route,
    )
    route = re.sub(r"<(?:str|slug):report_name>", "sales", route)
    route = re.sub(r"<(?:str|slug):[^>]+>", "security-test-reference", route)
    return f"/{route}"


class ApiSecurityPolicyTests(SimpleTestCase):
    def test_every_api_view_has_an_explicit_reviewed_permission_policy(self):
        policies = {
            **{name: AllowAny for name in PUBLIC_VIEWS},
            **{name: IsAuthenticated for name in CUSTOMER_VIEWS},
            **{name: IsOwner for name in OWNER_VIEWS},
            **{
                name: IsOwnerOrAssignedBranchStaff
                for name in BRANCH_SCOPED_VIEWS
            },
        }
        discovered = {}

        for route, view_class in api_views(get_resolver().url_patterns):
            name = view_class.__name__
            discovered.setdefault(name, []).append(route)
            self.assertIn(
                "permission_classes",
                view_class.__dict__,
                f"{route} ({name}) must declare permission_classes explicitly.",
            )
            self.assertIn(
                name,
                policies,
                f"{route} ({name}) has not been classified in the API security policy.",
            )
            self.assertIn(
                policies[name],
                view_class.permission_classes,
                f"{route} ({name}) does not enforce its reviewed policy.",
            )
            if name not in PUBLIC_VIEWS:
                self.assertNotIn(
                    AllowAny,
                    view_class.permission_classes,
                    f"Protected endpoint {route} ({name}) must not allow anonymous access.",
                )

        classified = PUBLIC_VIEWS | CUSTOMER_VIEWS | OWNER_VIEWS | BRANCH_SCOPED_VIEWS
        self.assertSetEqual(
            set(discovered),
            classified,
            "The security registry and mounted /api/v1 routes have drifted.",
        )

    def test_management_and_pos_routes_are_never_public_or_customer_only(self):
        for route, view_class in api_views(get_resolver().url_patterns):
            if "/management/" not in route and not route.startswith(
                ("api/v1/reports/", "api/v1/pos/")
            ):
                continue
            self.assertTrue(
                IsOwner in view_class.permission_classes
                or IsOwnerOrAssignedBranchStaff in view_class.permission_classes,
                f"Privileged route {route} has no management permission class.",
            )


class CustomerManagementEndpointDenialTests(TestCase):
    """Prove a normal customer is rejected by every privileged API route."""

    def setUp(self):
        self.customer = User.objects.create_user(
            email="security-customer@example.com",
            phone_number="+233241370499",
            full_name="Security Test Customer",
            password="CustomerPass123!",
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.customer)

    def test_customer_cannot_access_any_management_report_or_pos_endpoint(self):
        privileged_routes = [
            route
            for route, _view_class in api_views(get_resolver().url_patterns)
            if "/management/" in route
            or route.startswith(("api/v1/reports/", "api/v1/pos/"))
        ]
        self.assertTrue(privileged_routes, "No privileged API routes were discovered.")

        for route in privileged_routes:
            with self.subTest(route=route):
                response = self.client.get(concrete_test_path(route))
                self.assertEqual(
                    response.status_code,
                    403,
                    f"Customer unexpectedly reached privileged endpoint {route}.",
                )
