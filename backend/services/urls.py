from django.urls import path

from .views import (
    FeaturedServiceListView,
    ManagementServiceBranchOptionListView,
    ManagementServiceCategoryOptionListView,
    ManagementServiceCategoryDetailView,
    ManagementServiceCategoryListCreateView,
    ManagementServiceDetailView,
    ManagementServiceListView,
    PublicServiceCategoryListView,
    PublicServiceDetailView,
    PublicServiceListView,
)


app_name = "services"

urlpatterns = [
    path("", PublicServiceListView.as_view(), name="list"),
    path("categories/", PublicServiceCategoryListView.as_view(), name="categories"),
    path("featured/", FeaturedServiceListView.as_view(), name="featured"),
    path(
        "management/category-options/",
        ManagementServiceCategoryOptionListView.as_view(),
        name="management-category-options",
    ),
    path(
        "management/service-categories/",
        ManagementServiceCategoryListCreateView.as_view(),
        name="management-category-list",
    ),
    path(
        "management/service-categories/<uuid:pk>/",
        ManagementServiceCategoryDetailView.as_view(),
        name="management-category-detail",
    ),
    path(
        "management/branch-options/",
        ManagementServiceBranchOptionListView.as_view(),
        name="management-branch-options",
    ),
    path("management/", ManagementServiceListView.as_view(), name="management-list"),
    path(
        "management/<uuid:pk>/",
        ManagementServiceDetailView.as_view(),
        name="management-detail",
    ),
    path("<slug:slug>/", PublicServiceDetailView.as_view(), name="detail"),
]
