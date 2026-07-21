from django.contrib import admin

from .models import Product, ProductCategory, ProductVariant


@admin.register(ProductCategory)
class ProductCategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "display_order", "is_active")
    list_editable = ("display_order", "is_active")
    prepopulated_fields = {"slug": ("name",)}
    search_fields = ("name",)


class ProductVariantInline(admin.TabularInline):
    model = ProductVariant
    extra = 0
    show_change_link = True


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "brand",
        "category",
        "is_featured",
        "is_published",
        "is_active",
    )
    list_filter = ("category", "brand", "is_featured", "is_published", "is_active")
    search_fields = ("name", "brand", "description", "variants__sku")
    prepopulated_fields = {"slug": ("name",)}
    readonly_fields = ("id", "created_at", "updated_at")
    inlines = (ProductVariantInline,)


@admin.register(ProductVariant)
class ProductVariantAdmin(admin.ModelAdmin):
    list_display = (
        "sku",
        "product",
        "name",
        "selling_price",
        "cost_price",
        "is_preorder",
        "is_active",
    )
    list_filter = ("is_preorder", "is_active", "product__category")
    search_fields = ("sku", "product__name", "name")
    readonly_fields = ("id", "created_at", "updated_at")
