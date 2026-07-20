from django.conf import settings
from django.db import connection
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response


@api_view(["GET"])
@permission_classes([AllowAny])
def health_check(request):
    database_status = "connected"

    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            cursor.fetchone()
    except Exception:
        database_status = "disconnected"

    return Response(
        {
            "application": "Golden Touch Beauty Centre",
            "status": "ok",
            "database": database_status,
            "debug": settings.DEBUG,
        }
    )