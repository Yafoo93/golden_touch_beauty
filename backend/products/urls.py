from django.urls import path

from .views import (
    CartValidationView,
    CustomerCartItemView,
    CustomerCartItemDetailView,
    CustomerCartView,
    FeaturedProductListView,
    ManagementProductListView,
    ManagementProductBranchOptionListView,
    ManagementProductCategoryOptionListView,
    ManagementProductCategoryDetailView,
    ManagementProductCategoryListCreateView,
    ManagementProductDetailView,
    PublicProductCategoryListView,
    PublicProductDetailView,
    PublicProductListView,
    WishlistItemDetailView,
    WishlistView,
)


app_name = "products"

urlpatterns = [
    path("", PublicProductListView.as_view(), name="list"),
    path("categories/", PublicProductCategoryListView.as_view(), name="categories"),
    path("featured/", FeaturedProductListView.as_view(), name="featured"),
    path("wishlist/", WishlistView.as_view(), name="wishlist"),
    path("cart/", CustomerCartView.as_view(), name="customer-cart"),
    path("cart/items/", CustomerCartItemView.as_view(), name="customer-cart-items"),
    path(
        "cart/items/<uuid:variant_id>/",
        CustomerCartItemDetailView.as_view(),
        name="customer-cart-item-detail",
    ),
    path("cart/validate/", CartValidationView.as_view(), name="cart-validate"),
    path(
        "wishlist/<slug:product_slug>/",
        WishlistItemDetailView.as_view(),
        name="wishlist-item",
    ),
    path("management/", ManagementProductListView.as_view(), name="management-list"),
    path(
        "management/category-options/",
        ManagementProductCategoryOptionListView.as_view(),
        name="management-category-options",
    ),
    path(
        "management/product-categories/",
        ManagementProductCategoryListCreateView.as_view(),
        name="management-product-category-list",
    ),
    path(
        "management/product-categories/<uuid:pk>/",
        ManagementProductCategoryDetailView.as_view(),
        name="management-product-category-detail",
    ),
    path(
        "management/branch-options/",
        ManagementProductBranchOptionListView.as_view(),
        name="management-branch-options",
    ),
    path(
        "management/<uuid:pk>/",
        ManagementProductDetailView.as_view(),
        name="management-detail",
    ),
    path("<slug:slug>/", PublicProductDetailView.as_view(), name="detail"),
]
