from django.urls import path

from .views import (
    BookingAvailabilityView,
    CustomerBookingDetailView,
    CustomerBookingListCreateView,
    CustomerBookingProposalView,
    ManagementBookingActionView,
    ManagementBookingBlockDetailView,
    ManagementBookingBlockListCreateView,
    ManagementBookingDetailView,
    ManagementBookingListCreateView,
    ManagementBookingOptionsView,
)

app_name = "bookings"

urlpatterns = [
    path("", CustomerBookingListCreateView.as_view(), name="customer-list"),
    path("availability/", BookingAvailabilityView.as_view(), name="availability"),
    path("<str:reference>/", CustomerBookingDetailView.as_view(), name="customer-detail"),
    path("<str:reference>/proposal/", CustomerBookingProposalView.as_view(), name="customer-proposal"),
    path("management/all/", ManagementBookingListCreateView.as_view(), name="management-list"),
    path("management/options/", ManagementBookingOptionsView.as_view(), name="management-options"),
    path("management/blocks/", ManagementBookingBlockListCreateView.as_view(), name="management-blocks"),
    path("management/blocks/<uuid:pk>/", ManagementBookingBlockDetailView.as_view(), name="management-block-detail"),
    path("management/<str:reference>/", ManagementBookingDetailView.as_view(), name="management-detail"),
    path("management/<str:reference>/action/", ManagementBookingActionView.as_view(), name="management-action"),
]
