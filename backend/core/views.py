from django.db import connection
from drf_spectacular.utils import extend_schema, inline_serializer
from rest_framework import serializers
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from .exceptions import error_payload


@extend_schema(
    responses=inline_serializer(
        name="HealthResponse",
        fields={
            "application": serializers.CharField(),
            "status": serializers.CharField(),
            "database": serializers.CharField(),
        },
    )
)
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
        }
    )


@api_view(["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"])
@permission_classes([AllowAny])
def api_not_found(request, path=None):
    return Response(
        error_payload(
            code="not_found",
            message="The requested API endpoint was not found.",
            status_code=404,
        ),
        status=404,
    )
