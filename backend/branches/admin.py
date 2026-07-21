from django.contrib import admin

from .models import Branch


@admin.register(Branch)
class BranchAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "code",
        "telephone_number",
        "secondary_telephone_number",
        "opening_time",
        "closing_time",
        "assigned_manager",
        "is_active",
    )
    list_filter = ("is_active",)
    search_fields = (
        "name",
        "code",
        "address",
        "telephone_number",
        "secondary_telephone_number",
    )
    readonly_fields = ("id", "created_at", "updated_at")

# Register your models here.
