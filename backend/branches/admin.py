from django.contrib import admin

from .models import Branch, BranchStaffAssignment


class BranchStaffAssignmentInline(admin.TabularInline):
    model = BranchStaffAssignment
    extra = 0
    autocomplete_fields = ("staff", "assigned_by")
    fields = ("staff", "roles", "permission_overrides", "is_active", "assigned_by")


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
    inlines = (BranchStaffAssignmentInline,)


@admin.register(BranchStaffAssignment)
class BranchStaffAssignmentAdmin(admin.ModelAdmin):
    list_display = ("staff", "branch", "display_roles", "is_active", "assigned_by", "updated_at")
    list_filter = ("branch", "is_active")
    search_fields = ("staff__full_name", "staff__email", "branch__name", "branch__code")
    autocomplete_fields = ("branch", "staff", "assigned_by")
    readonly_fields = ("id", "created_at", "updated_at")

    @admin.display(description="Roles")
    def display_roles(self, assignment):
        labels = dict(BranchStaffAssignment.Role.choices)
        return ", ".join(labels.get(role, role) for role in assignment.roles)

# Register your models here.
