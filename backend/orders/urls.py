from django.urls import path

from .views import (
    CheckoutCreateView,
    CheckoutOptionsView,
    CustomerOrderCancelView,
    CustomerOrderDetailView,
    CustomerOrderListView,
)

app_name = "orders"

urlpatterns = [
    path("", CustomerOrderListView.as_view(), name="customer-list"),
    path("checkout/options/", CheckoutOptionsView.as_view(), name="checkout-options"),
    path("checkout/", CheckoutCreateView.as_view(), name="checkout-create"),
    path("<str:reference>/", CustomerOrderDetailView.as_view(), name="customer-detail"),
    path("<str:reference>/cancel/", CustomerOrderCancelView.as_view(), name="customer-cancel"),
]
