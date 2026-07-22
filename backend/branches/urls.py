from django.urls import path

from .views import (
    BranchManagerOptionListView,
    ManagementBranchDetailView,
    ManagementBranchListView,
    PickupBranchOptionsView,
    PublicBranchDetailView,
    PublicBranchListView,
)


app_name = "branches"

urlpatterns = [
    path("", PublicBranchListView.as_view(), name="public-list"),
    path("management/", ManagementBranchListView.as_view(), name="management-list"),
    path("management/managers/", BranchManagerOptionListView.as_view(), name="management-manager-options"),
    path("management/<uuid:pk>/", ManagementBranchDetailView.as_view(), name="management-detail"),
    path("pickup-options/", PickupBranchOptionsView.as_view(), name="pickup-options"),
    path("<uuid:pk>/", PublicBranchDetailView.as_view(), name="public-detail"),
]
