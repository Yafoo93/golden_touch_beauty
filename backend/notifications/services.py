from .models import Notification


def create_notification(
    *, recipient, category, title, message, action_url, event_key
):
    """Create an idempotent operational notification for one customer."""
    if not recipient or not getattr(recipient, "pk", None):
        return None
    notification, _ = Notification.objects.get_or_create(
        event_key=event_key,
        defaults={
            "recipient": recipient,
            "category": category,
            "title": title,
            "message": message,
            "action_url": action_url,
        },
    )
    return notification
