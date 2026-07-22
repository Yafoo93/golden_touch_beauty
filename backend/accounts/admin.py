from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    ordering = ("email",)

    list_display = (
        "email",
        "phone_number",
        "full_name",
        "email_verified_at",
        "is_staff",
        "is_active",
    )

    list_filter = (
        "is_staff",
        "is_superuser",
        "is_active",
        "gender",
    )

    search_fields = (
        "email",
        "phone_number",
        "full_name",
    )

    readonly_fields = (
        "last_login",
        "created_at",
        "updated_at",
        "email_verified_at",
    )

    fieldsets = (
        (
            None,
            {
                "fields": (
                    "email",
                    "phone_number",
                    "password",
                )
            },
        ),
        (
            "Personal information",
            {
                "fields": (
                    "full_name",
                    "date_of_birth",
                    "gender",
                    "email_verified_at",
                )
            },
        ),
        (
            "Permissions",
            {
                "fields": (
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "groups",
                    "user_permissions",
                )
            },
        ),
        (
            "System information",
            {
                "fields": (
                    "last_login",
                    "created_at",
                    "updated_at",
                )
            },
        ),
    )

    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": (
                    "email",
                    "phone_number",
                    "full_name",
                    "password1",
                    "password2",
                    "is_staff",
                    "is_active",
                ),
            },
        ),
    )
