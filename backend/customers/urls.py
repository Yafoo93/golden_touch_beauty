from django.urls import path

from .views import CustomerAccountOverviewView, CustomerAddressDetailView, CustomerAddressListCreateView, CustomerConsentView


app_name = "customers"

urlpatterns = [
    path("overview/", CustomerAccountOverviewView.as_view(), name="overview"),
    path("addresses/", CustomerAddressListCreateView.as_view(), name="address-list"),
    path("addresses/<uuid:pk>/", CustomerAddressDetailView.as_view(), name="address-detail"),
    path("consent/", CustomerConsentView.as_view(), name="consent"),
]
