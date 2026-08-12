from django.utils import timezone
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Notification
from .serializers import NotificationSerializer


def customer_notifications(user):
    return Notification.objects.filter(recipient=user)


class NotificationListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        queryset = customer_notifications(request.user)
        category = request.query_params.get("category", "").strip().lower()
        read_state = request.query_params.get("read", "").strip().lower()
        if category in Notification.Category.values:
            queryset = queryset.filter(category=category)
        if read_state == "unread":
            queryset = queryset.filter(read_at__isnull=True)
        elif read_state == "read":
            queryset = queryset.filter(read_at__isnull=False)
        try:
            limit = min(max(int(request.query_params.get("limit", 10)), 1), 50)
            offset = max(int(request.query_params.get("offset", 0)), 0)
        except (TypeError, ValueError):
            limit = 10
            offset = 0
        total = queryset.count()
        return Response(
            {
                "notifications": NotificationSerializer(
                    queryset[offset:offset + limit], many=True
                ).data,
                "unread_count": customer_notifications(request.user).filter(
                    read_at__isnull=True
                ).count(),
                "total": total,
                "offset": offset,
                "limit": limit,
                "has_more": offset + limit < total,
            }
        )


class NotificationReadView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, notification_id):
        notification = customer_notifications(request.user).filter(
            pk=notification_id
        ).first()
        if notification is None:
            return Response(
                {"detail": "Notification was not found."},
                status=status.HTTP_404_NOT_FOUND,
            )
        notification.mark_read()
        return Response(NotificationSerializer(notification).data)


class NotificationReadAllView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        updated = customer_notifications(request.user).filter(
            read_at__isnull=True
        ).update(read_at=timezone.now(), updated_at=timezone.now())
        return Response({"updated": updated, "unread_count": 0})
