import logging
from collections.abc import Mapping, Sequence

from django.core.exceptions import PermissionDenied as DjangoPermissionDenied
from django.http import Http404
from rest_framework import exceptions, serializers, status
from rest_framework.response import Response
from rest_framework.views import exception_handler as drf_exception_handler


logger = logging.getLogger(__name__)


class Conflict(exceptions.APIException):
    status_code = status.HTTP_409_CONFLICT
    default_detail = "The request conflicts with the current resource state."
    default_code = "conflict"


class BusinessRuleViolation(exceptions.APIException):
    status_code = status.HTTP_422_UNPROCESSABLE_ENTITY
    default_detail = "The request violates a business rule."
    default_code = "business_rule_violation"


def _to_plain_value(value):
    """Convert DRF ErrorDetail and nested values into JSON-safe primitives."""

    if isinstance(value, Mapping):
        return {str(key): _to_plain_value(item) for key, item in value.items()}
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
        return [_to_plain_value(item) for item in value]
    return str(value) if isinstance(value, exceptions.ErrorDetail) else value


def _error_code(exc):
    if isinstance(exc, serializers.ValidationError):
        return "validation_error"
    if isinstance(exc, (exceptions.NotAuthenticated, exceptions.AuthenticationFailed)):
        return "not_authenticated"
    if isinstance(exc, (exceptions.PermissionDenied, DjangoPermissionDenied)):
        return "permission_denied"
    if isinstance(exc, (exceptions.NotFound, Http404)):
        return "not_found"
    if isinstance(exc, exceptions.MethodNotAllowed):
        return "method_not_allowed"
    if isinstance(exc, exceptions.Throttled):
        return "rate_limited"
    if isinstance(exc, exceptions.ParseError):
        return "invalid_json"
    if isinstance(exc, exceptions.UnsupportedMediaType):
        return "unsupported_media_type"
    if isinstance(exc, exceptions.APIException):
        codes = exc.get_codes()
        return codes if isinstance(codes, str) else exc.default_code
    return "server_error"


def _error_message(exc, code, response_data):
    messages = {
        "validation_error": "Some submitted information is invalid.",
        "not_authenticated": "Authentication is required for this request.",
        "permission_denied": "You do not have permission to perform this action.",
        "not_found": "The requested resource was not found.",
        "method_not_allowed": "This request method is not allowed.",
        "rate_limited": "Too many requests. Please try again later.",
        "invalid_json": "The request body contains invalid JSON.",
        "unsupported_media_type": "The request content type is not supported.",
        "conflict": "The request conflicts with the current resource state.",
        "business_rule_violation": "The request violates a business rule.",
        "server_error": "An unexpected error occurred. Please try again later.",
    }
    if code in messages:
        return messages[code]
    if isinstance(response_data, Mapping) and "detail" in response_data:
        return str(response_data["detail"])
    return str(getattr(exc, "detail", "The request could not be completed."))


def error_payload(*, code, message, status_code, details=None):
    return {
        "error": {
            "code": code,
            "message": message,
            "status": status_code,
            "details": _to_plain_value(details or {}),
        }
    }


def api_exception_handler(exc, context):
    """Return the same safe error envelope for every REST API failure."""

    response = drf_exception_handler(exc, context)

    if response is None:
        request = context.get("request")
        logger.error(
            "Unhandled API exception on %s %s",
            getattr(request, "method", "UNKNOWN"),
            getattr(request, "path", "UNKNOWN"),
            exc_info=(type(exc), exc, exc.__traceback__),
        )
        return Response(
            error_payload(
                code="server_error",
                message="An unexpected error occurred. Please try again later.",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            ),
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    code = _error_code(exc)
    original_data = response.data
    response.data = error_payload(
        code=code,
        message=_error_message(exc, code, original_data),
        status_code=response.status_code,
        details=original_data,
    )
    return response
