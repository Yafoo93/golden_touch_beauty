from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path, re_path
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularRedocView,
    SpectacularSwaggerView,
)

from core.views import api_not_found


urlpatterns = [
    path("admin/", admin.site.urls),

    path("api/v1/", include("core.urls")),
    path("api/v1/auth/", include("accounts.urls")),
    path("api/v1/account/", include("customers.urls")),
    path("api/v1/branches/", include("branches.urls")),
    path("api/v1/services/", include("services.urls")),
    path("api/v1/products/", include("products.urls")),
    path("api/v1/inventory/", include("inventory.urls")),
    path("api/v1/bookings/", include("bookings.urls")),
    path("api/v1/orders/", include("orders.urls")),
    path("api/v1/payments/", include("payments.urls")),
    path("api/v1/notifications/", include("notifications.urls")),
    path("api/v1/pos/", include("pos.urls")),
    path("api/v1/reports/", include("reports.urls")),

    path(
        "api/schema/",
        SpectacularAPIView.as_view(),
        name="api-schema",
    ),
    path(
        "api/docs/",
        SpectacularSwaggerView.as_view(url_name="api-schema"),
        name="swagger-ui",
    ),
    path(
        "api/redoc/",
        SpectacularRedocView.as_view(url_name="api-schema"),
        name="redoc",
    ),
    re_path(r"^api/(?P<path>.*)$", api_not_found, name="api-not-found"),
]

if settings.DEBUG:
    urlpatterns += static(
        settings.MEDIA_URL,
        document_root=settings.MEDIA_ROOT,
    )
