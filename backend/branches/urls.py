from django.urls import path

from .views import (
    PickupBranchOptionsView,
    PublicBranchDetailView,
    PublicBranchListView,
)


app_name = "branches"

urlpatterns = [
    path("", PublicBranchListView.as_view(), name="public-list"),
    path("pickup-options/", PickupBranchOptionsView.as_view(), name="pickup-options"),
    path("<uuid:pk>/", PublicBranchDetailView.as_view(), name="public-detail"),
]
