from django.urls import path

from .views import health_check, report_client_error


app_name = "core"

urlpatterns = [
    path("health/", health_check, name="health-check"),
    path("client-errors/", report_client_error, name="client-error-report"),
]
