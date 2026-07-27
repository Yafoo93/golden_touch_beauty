from django.urls import path

from .views import (
    ManagementGalleryItemDetailView,
    ManagementGalleryItemListCreateView,
    ManagementTestimonialDetailView,
    ManagementTestimonialListView,
    ManagementWebsiteContentDetailView,
    ManagementWebsiteContentListView,
    PublicGalleryItemListView,
    PublicTestimonialListView,
    PublicWebsiteContentListView,
    health_check,
    ping,
    report_client_error,
)


app_name = "core"

urlpatterns = [
    path("ping/", ping, name="ping"),
    path("health/", health_check, name="health-check"),
    path("client-errors/", report_client_error, name="client-error-report"),
    path("content/", PublicWebsiteContentListView.as_view(), name="public-content"),
    path("gallery/", PublicGalleryItemListView.as_view(), name="public-gallery"),
    path(
        "testimonials/",
        PublicTestimonialListView.as_view(),
        name="public-testimonials",
    ),
    path(
        "testimonials/management/",
        ManagementTestimonialListView.as_view(),
        name="management-testimonial-list",
    ),
    path(
        "testimonials/management/<uuid:pk>/",
        ManagementTestimonialDetailView.as_view(),
        name="management-testimonial-detail",
    ),
    path(
        "gallery/management/",
        ManagementGalleryItemListCreateView.as_view(),
        name="management-gallery-list",
    ),
    path(
        "gallery/management/<uuid:pk>/",
        ManagementGalleryItemDetailView.as_view(),
        name="management-gallery-detail",
    ),
    path(
        "content/management/",
        ManagementWebsiteContentListView.as_view(),
        name="management-content-list",
    ),
    path(
        "content/management/<uuid:pk>/",
        ManagementWebsiteContentDetailView.as_view(),
        name="management-content-detail",
    ),
]
