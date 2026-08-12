from django.contrib import admin

from .models import EmailJob, Notification


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ("title", "recipient", "category", "read_at", "created_at")
    list_filter = ("category", "read_at")
    search_fields = ("title", "message", "recipient__email", "event_key")
    readonly_fields = (
        "recipient", "category", "title", "message", "action_url",
        "event_key", "read_at", "created_at", "updated_at",
    )


@admin.register(EmailJob)
class EmailJobAdmin(admin.ModelAdmin):
    list_display = (
        "job_type", "status", "attempts", "next_attempt_at", "completed_at"
    )
    list_filter = ("status", "job_type")
    search_fields = ("unique_key", "last_error")
    readonly_fields = (
        "job_type", "object_id", "event", "payload", "unique_key", "status",
        "attempts", "max_attempts", "next_attempt_at", "started_at",
        "completed_at", "last_error", "created_at", "updated_at",
    )
