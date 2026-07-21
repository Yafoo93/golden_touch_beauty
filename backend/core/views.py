import logging

from django.db import connection
from drf_spectacular.utils import extend_schema, inline_serializer
from rest_framework import serializers
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from .exceptions import error_payload


logger = logging.getLogger("golden_touch.health")


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
        logger.exception("database_health_check_failed")

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
            request_id=getattr(request, "request_id", None),
        ),
        status=404,
    )


class ClientErrorSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=100, required=False, default="Error")
    message = serializers.CharField(max_length=500)
    digest = serializers.CharField(max_length=200, required=False, allow_blank=True)
    path = serializers.CharField(max_length=500, required=False, allow_blank=True)


@extend_schema(
    request=ClientErrorSerializer,
    responses={202: None},
)
@api_view(["POST"])
@permission_classes([AllowAny])
def report_client_error(request):
    serializer = ClientErrorSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    data = serializer.validated_data
    logger.error(
        "client_error_reported",
        extra={
            "error_name": data["name"],
            "error_message": data["message"],
            "error_digest": data.get("digest", ""),
            "client_path": data.get("path", ""),
        },
    )
    return Response(status=202)
