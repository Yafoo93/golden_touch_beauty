from django.contrib import admin

from .models import AuditLog


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = (
        "created_at",
        "actor",
        "actor_role",
        "action",
        "record_type",
        "record_id",
        "branch",
    )
    list_filter = ("action", "record_type", "branch", "created_at")
    search_fields = (
        "actor__email",
        "actor__phone_number",
        "record_id",
        "device_identifier",
        "reason",
    )
    readonly_fields = [field.name for field in AuditLog._meta.fields]

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

# Register your models here.
