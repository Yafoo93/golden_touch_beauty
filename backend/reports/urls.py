from django.urls import path

from .views import ManagementBookingsReportView, ManagementBranchesReportView, ManagementInventoryReportView, ManagementPaymentsReportView, ManagementProductsReportView, ManagementReportExportView, ManagementSalesReportView, ManagementServicesReportView

app_name = "reports"

urlpatterns = [
    path("<str:report_name>/export/", ManagementReportExportView.as_view(), name="export"),
    path("sales/", ManagementSalesReportView.as_view(), name="sales"),
    path("bookings/", ManagementBookingsReportView.as_view(), name="bookings"),
    path("products/", ManagementProductsReportView.as_view(), name="products"),
    path("services/", ManagementServicesReportView.as_view(), name="services"),
    path("inventory/", ManagementInventoryReportView.as_view(), name="inventory"),
    path("payments/", ManagementPaymentsReportView.as_view(), name="payments"),
    path("branches/", ManagementBranchesReportView.as_view(), name="branches"),
]
