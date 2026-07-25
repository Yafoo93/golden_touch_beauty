from .models import AuditLog


def record_event(
    *,
    action,
    record_type,
    record_id,
    actor=None,
    actor_role="",
    branch=None,
    previous_values=None,
    new_values=None,
    ip_address=None,
    device_identifier="",
    reason="",
):
    AuditLog.objects.create(
        actor=actor,
        actor_role=actor_role,
        action=action,
        record_type=record_type,
        record_id=str(record_id),
        previous_values=previous_values or {},
        new_values=new_values or {},
        branch=branch,
        ip_address=ip_address,
        device_identifier=device_identifier[:255],
        reason=reason,
    )


def actor_role_for(user):
    if user is None:
        return ""
    if user.is_superuser or user.is_staff:
        return "staff"
    return "customer"


def client_ip(request):
    return request.META.get("REMOTE_ADDR")


def client_device(request):
    return request.META.get("HTTP_USER_AGENT", "")[:255]
