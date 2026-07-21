from django.contrib import admin

from .models import IdempotencyRecord


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

# Register your models here.
