from django.urls import path

from .views import POSEndOfDayView, POSCustomerSearchView, POSSaleCorrectionView, POSSaleDetailView, POSSaleHistoryView, POSWorkspaceView

app_name = "pos"

urlpatterns = [
    path("workspace/", POSWorkspaceView.as_view(), name="workspace"),
    path("customers/", POSCustomerSearchView.as_view(), name="customer-search"),
    path("sales/", POSSaleHistoryView.as_view(), name="sales"),
    path("sales/<str:reference>/", POSSaleDetailView.as_view(), name="sale-detail"),
    path("sales/<str:reference>/corrections/", POSSaleCorrectionView.as_view(), name="sale-correction"),
    path("end-of-day/", POSEndOfDayView.as_view(), name="end-of-day"),
]
