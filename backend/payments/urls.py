from django.urls import path

from .views import CustomerReceiptDetailView, CustomerReceiptListView


app_name = "payments"

urlpatterns = [
    path("receipts/", CustomerReceiptListView.as_view(), name="receipt-list"),
    path(
        "receipts/<str:reference>/",
        CustomerReceiptDetailView.as_view(),
        name="receipt-detail",
    ),
]
