from django.contrib import admin

from .models import GalleryItem, IdempotencyRecord, Testimonial, WebsiteContent


@admin.register(IdempotencyRecord)
class IdempotencyRecordAdmin(admin.ModelAdmin):
    list_display = (
        "scope",
        "key",
        "response_status",
        "completed_at",
        "expires_at",
    )
    list_filter = ("scope", "response_status")
    search_fields = ("scope", "key", "request_hash")
    readonly_fields = (
        "id",
        "scope",
        "key",
        "request_hash",
        "response_status",
        "response_body",
        "completed_at",
        "expires_at",
        "created_at",
        "updated_at",
    )

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

@admin.register(WebsiteContent)
class WebsiteContentAdmin(admin.ModelAdmin):
    list_display = ("label", "page", "section", "is_published", "updated_at")
    list_filter = ("page", "section", "is_published")
    search_fields = ("key", "label", "value")
    readonly_fields = ("key", "page", "section", "label", "updated_by")

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(GalleryItem)
class GalleryItemAdmin(admin.ModelAdmin):
    list_display = ("title", "category", "display_order", "is_published", "updated_at")
    list_editable = ("display_order", "is_published")
    list_filter = ("category", "display_size", "is_published")
    search_fields = ("title", "category", "alt_text")


@admin.register(Testimonial)
class TestimonialAdmin(admin.ModelAdmin):
    list_display = (
        "client_name", "service_context", "moderation_status",
        "consent_confirmed", "is_visible", "reviewed_at",
    )
    list_filter = (
        "moderation_status", "consent_confirmed", "is_visible",
        "is_featured", "source_type",
    )
    search_fields = ("client_name", "service_context", "quote")
    readonly_fields = ("reviewed_by", "reviewed_at")
