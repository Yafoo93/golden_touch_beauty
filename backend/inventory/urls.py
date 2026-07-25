from django.urls import path

from .views import (
    ManagementInventoryListView,
    ManagementStockAdjustmentView,
    ManagementVariantStockHistoryView,
)


app_name = "inventory"

urlpatterns = [
    path(
        "management/",
        ManagementInventoryListView.as_view(),
        name="management-list",
    ),
    path(
        "management/<uuid:variant_id>/",
        ManagementVariantStockHistoryView.as_view(),
        name="management-variant-history",
    ),
    path(
        "management/adjustments/",
        ManagementStockAdjustmentView.as_view(),
        name="management-adjustment",
    ),
]
